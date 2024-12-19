from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import asyncio
from asgiref.wsgi import WsgiToAsgi
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from models.models import db, User, App, ScoreConsumption, ScoreTransfer
import os
import json
import httpx
import secrets
from datetime import datetime, timedelta
import jwt
from functools import wraps
from urllib.parse import urlencode

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///scores.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# OAuth2配置
oauth = OAuth(app)
oauth.register(
    name='linux_do',
    client_id=os.getenv('OAUTH_CLIENT_ID'),
    client_secret=os.getenv('OAUTH_CLIENT_SECRET'),
    access_token_url='https://connect.linux.do/oauth2/token',
    access_token_params=None,
    authorize_url='https://connect.linux.do/oauth2/authorize',
    authorize_params=None,
    api_base_url='https://connect.linux.do/api/',
    client_kwargs={'scope': 'user'},
)

# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
                         error_code=404,
                         error_message="页面未找到"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html',
                         error_code=500,
                         error_message="服务器内部错误"), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html',
                         error_code=403,
                         error_message="没有权限访问此页面"), 403

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_jwt_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def require_app_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            return jsonify({'error': '缺少认证信息'}), 401
        
        try:
            client_id, client_secret = auth.split(':')
            app = App.query.filter_by(
                client_id=client_id,
                client_secret=client_secret
            ).first()
            
            if not app:
                return jsonify({'error': '无效的应用认证信息'}), 401
                
            # 将app对象添加到请求上下文
            request.current_app = app
            return f(*args, **kwargs)
        except ValueError:
            return jsonify({'error': '认证格式错误'}), 401
        except Exception as e:
            app.logger.error(f"API认证错误: {str(e)}")
            return jsonify({'error': '认证失败'}), 401
            
    return decorated

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    redirect_uri = url_for('oauth2_callback', _external=True)
    return oauth.linux_do.authorize_redirect(redirect_uri)

@app.route('/oauth2/callback')
def oauth2_callback():
    token = oauth.linux_do.authorize_access_token()
    resp = oauth.linux_do.get('user')
    user_info = resp.json()
    
    # 获取用户点数
    def get_score():
        try:
            import requests
            session = requests.Session()
            session.verify = False
            
            # 全局代理配置
            use_proxy = os.getenv('USE_PROXY', 'false').lower() == 'true'
            if use_proxy:
                proxy = os.getenv('HTTP_PROXY')
                if proxy:
                    session.proxies = {
                        "http": proxy,
                        "https": proxy
                    }
                    app.logger.info(f"使用代理获取用户 {user_info['username']} 的点数信息")
            else:
                app.logger.info(f"开始获取用户 {user_info['username']} 的点数信息")
            
            score_resp = session.get(
                f"https://linux.do/u/{user_info['username']}.json",
                timeout=30.0
            )
            score_resp.raise_for_status()
            score_data = score_resp.json()
            
            if not score_data or 'user' not in score_data:
                raise ValueError("响应数据格式错误")
                
            return score_data['user'].get('gamification_score', 0)
            
        except Exception as e:
            app.logger.error(f"获取用户点数失败: {str(e)}")
            return 0
    
    gamification_score = get_score()
    
    user = User.query.filter_by(forum_id=user_info['id']).first()
    if user:
        user.username = user_info['username']
        user.name = user_info['name']
        user.trust_level = user_info['trust_level']
        user.original_score = gamification_score
        if user.actual_score == 0:  # 如果是首次登录
            user.actual_score = gamification_score
    else:
        user = User(
            forum_id=user_info['id'],
            username=user_info['username'],
            name=user_info['name'],
            trust_level=user_info['trust_level'],
            original_score=gamification_score,
            actual_score=gamification_score
        )
        db.session.add(user)
    
    db.session.commit()
    login_user(user)
    
    # 创建JWT token并存储在cookie中
    token = create_jwt_token(user.id)
    response = redirect(url_for('dashboard'))
    response.set_cookie('jwt_token', token, httponly=True, max_age=7*24*60*60)
    return response

@app.route('/dashboard')
@login_required
def dashboard():
    # 获取消耗记录
    consumptions = ScoreConsumption.query.filter_by(user_id=current_user.id)\
        .order_by(ScoreConsumption.created_at.desc())\
        .all()
    
    # 获取转账记录（发送和接收）
    transfers = ScoreTransfer.query.filter(
        (ScoreTransfer.from_user_id == current_user.id) |
        (ScoreTransfer.to_user_id == current_user.id)
    ).order_by(ScoreTransfer.created_at.desc()).all()
    
    # 合并记录并按时间排序
    records = sorted(
        consumptions + transfers,
        key=lambda x: x.created_at,
        reverse=True
    )
    
    return render_template('dashboard.html', records=records)

@app.route('/developer')
@login_required
def developer():
    if current_user.trust_level < 1:
        flash('需要信任等级1以上才能访问开发者页面')
        return redirect(url_for('dashboard'))
    apps = App.query.filter_by(user_id=current_user.id).all()
    return render_template('developer.html', apps=apps)

@app.route('/playground')
@login_required
def playground():
    if current_user.trust_level < 1:
        flash('需要信任等级1以上才能访问API Playground')
        return redirect(url_for('dashboard'))
    apps = App.query.filter_by(user_id=current_user.id).all()
    return render_template('playground.html', apps=apps)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    response = redirect(url_for('index'))
    response.delete_cookie('jwt_token')
    return response

@app.route('/api/apps', methods=['POST'])
@login_required
def create_app():
    if current_user.trust_level < 1:
        return jsonify({'error': '需要信任等级1以上才能创建应用'}), 403
    
    data = request.json
    app = App(
        name=data['name'],
        description=data.get('description', ''),
        client_id=os.urandom(16).hex(),
        client_secret=os.urandom(32).hex(),
        redirect_uri=data['redirect_uri'],
        user_id=current_user.id
    )
    db.session.add(app)
    db.session.commit()
    return jsonify({
        'id': app.id,
        'client_id': app.client_id,
        'client_secret': app.client_secret
    })

def generate_confirm_token():
    """生成确认token"""
    return secrets.token_urlsafe(32)

@app.route('/confirm/<token>')
def confirm_page(token):
    """确认页面"""
    consumption = ScoreConsumption.query.filter_by(confirm_token=token, status='pending').first()
    if consumption:
        return render_template('confirm.html', 
                             operation='consume',
                             consumption=consumption,
                             is_popup='popup' in request.args)
    
    transfer = ScoreTransfer.query.filter_by(confirm_token=token, status='pending').first()
    if transfer:
        return render_template('confirm.html',
                             operation='transfer',
                             transfer=transfer,
                             is_popup='popup' in request.args)
    
    return render_template('error.html',
                         error_code=404,
                         error_message="无效或已使用的确认链接"), 404

@app.route('/confirm/consume/<token>', methods=['POST'])
@login_required
def confirm_consumption(token):
    """确认点数消耗"""
    consumption = ScoreConsumption.query.filter_by(
        confirm_token=token,
        status='pending',
        user_id=current_user.id
    ).first()
    
    if not consumption:
        return jsonify({'error': '无效或已使用的确认链接'}), 404
    
    action = request.form.get('action')
    if action == 'confirm':
        if current_user.actual_score < consumption.amount:
            return jsonify({'error': '点数不足', 'current_score': current_user.actual_score}), 400
        
        current_user.actual_score -= consumption.amount
        consumption.status = 'confirmed'
        consumption.confirmed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'username': current_user.username,
            'consumed': consumption.amount,
            'remaining_score': current_user.actual_score
        })
    elif action == 'reject':
        consumption.status = 'rejected'
        db.session.commit()
        return jsonify({
            'success': False,
            'error': '用户拒绝了操作'
        })
    
    return jsonify({'error': '无效的操作'}), 400

@app.route('/confirm/transfer/<token>', methods=['POST'])
@login_required
def confirm_transfer(token):
    """确认点数转账"""
    transfer = ScoreTransfer.query.filter_by(
        confirm_token=token,
        status='pending',
        from_user_id=current_user.id
    ).first()
    
    if not transfer:
        return jsonify({'error': '无效或已使用的确认链接'}), 404
    
    action = request.form.get('action')
    if action == 'confirm':
        if current_user.actual_score < transfer.amount:
            return jsonify({'error': '点数不足', 'current_score': current_user.actual_score}), 400
        
        current_user.actual_score -= transfer.amount
        transfer.to_user.actual_score += transfer.amount
        transfer.status = 'confirmed'
        transfer.confirmed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'from_username': current_user.username,
            'to_username': transfer.to_user.username,
            'amount': transfer.amount,
            'remaining_score': current_user.actual_score
        })
    elif action == 'reject':
        transfer.status = 'rejected'
        db.session.commit()
        return jsonify({
            'success': False,
            'error': '用户拒绝了操作'
        })
    
    return jsonify({'error': '无效的操作'}), 400

@app.route('/api/score/consume', methods=['POST'])
@require_app_auth
def consume_score():
    """请求消耗点数"""
    data = request.json
    if not data or 'username' not in data or 'amount' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    try:
        amount = int(data['amount'])
        if amount <= 0:
            return jsonify({'error': '消耗点数必须大于0'}), 400
            
        if user.actual_score < amount:
            return jsonify({'error': '用户点数不足', 'current_score': user.actual_score}), 400
        
        # 创建待确认的消耗记录
        consumption = ScoreConsumption(
            user_id=user.id,
            app_id=request.current_app.id,
            amount=amount,
            purpose=data.get('purpose', '未说明用途'),
            confirm_token=generate_confirm_token()
        )
        db.session.add(consumption)
        db.session.commit()
        
        # 生成确认URL
        confirm_url = url_for('confirm_page',
                            token=consumption.confirm_token,
                            _external=True)
        
        return jsonify({
            'success': True,
            'confirm_url': confirm_url,
            'consumption_id': consumption.id
        })
    except ValueError:
        return jsonify({'error': '无效的点数值'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"创建点数消耗请求失败: {str(e)}")
        return jsonify({'error': '操作失败'}), 500

@app.route('/api/score/transfer', methods=['POST'])
@login_required
def transfer_score():
    """转账点数"""
    data = request.json
    if not data or 'username' not in data or 'amount' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
        
    if data['username'] == current_user.username:
        return jsonify({'error': '不能转账给自己'}), 400
        
    to_user = User.query.filter_by(username=data['username']).first()
    if not to_user:
        return jsonify({'error': '用户不存在'}), 404
    
    try:
        amount = int(data['amount'])
        if amount <= 0:
            return jsonify({'error': '转账点数必须大于0'}), 400
            
        if current_user.actual_score < amount:
            return jsonify({'error': '点数不足', 'current_score': current_user.actual_score}), 400
        
        # 创建待确认的转账记录
        transfer = ScoreTransfer(
            from_user_id=current_user.id,
            to_user_id=to_user.id,
            amount=amount,
            message=data.get('message'),
            confirm_token=generate_confirm_token()
        )
        db.session.add(transfer)
        db.session.commit()
        
        # 生成确认URL
        confirm_url = url_for('confirm_page',
                            token=transfer.confirm_token,
                            _external=True)
        
        return jsonify({
            'success': True,
            'confirm_url': confirm_url,
            'transfer_id': transfer.id
        })
    except ValueError:
        return jsonify({'error': '无效的点数值'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"创建转账请求失败: {str(e)}")
        return jsonify({'error': '操作失败'}), 500

asgi_app = WsgiToAsgi(app)

if __name__ == '__main__':
    import uvicorn
    with app.app_context():
        db.create_all()
    uvicorn.run(asgi_app, host='0.0.0.0', port=8181)
