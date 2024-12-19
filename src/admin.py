from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from functools import wraps
from models.models import db, Admin, User, App, ScoreConsumption, ScoreTransfer
from werkzeug.security import generate_password_hash
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
login_manager = LoginManager()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(username=username, is_admin=True)
                db.session.add(user)
                db.session.commit()
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('用户名或密码错误')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    apps = App.query.all()
    consumptions = ScoreConsumption.query.all()
    transfers = ScoreTransfer.query.all()
    return render_template('admin/dashboard.html', 
                         users=users, 
                         apps=apps, 
                         consumptions=consumptions,
                         transfers=transfers)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.name = request.form.get('name')
        user.trust_level = int(request.form.get('trust_level'))
        user.original_score = int(request.form.get('original_score'))
        user.actual_score = int(request.form.get('actual_score'))
        db.session.commit()
        flash('用户信息已更新')
        return redirect(url_for('admin.users'))
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/apps')
@login_required
@admin_required
def apps():
    apps = App.query.all()
    return render_template('admin/apps.html', apps=apps)

@admin_bp.route('/app/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_app(id):
    app = App.query.get_or_404(id)
    if request.method == 'POST':
        app.name = request.form.get('name')
        app.description = request.form.get('description')
        app.redirect_uri = request.form.get('redirect_uri')
        db.session.commit()
        flash('应用信息已更新')
        return redirect(url_for('admin.apps'))
    return render_template('admin/edit_app.html', app=app)

@admin_bp.route('/consumptions')
@login_required
@admin_required
def consumptions():
    consumptions = ScoreConsumption.query.all()
    return render_template('admin/consumptions.html', consumptions=consumptions)

@admin_bp.route('/transfers')
@login_required
@admin_required
def transfers():
    transfers = ScoreTransfer.query.all()
    return render_template('admin/transfers.html', transfers=transfers)

def init_admin(app):
    """初始化管理员账号"""
    with app.app_context():
        admin_usernames = os.environ.get('ADMIN_USERNAME', '').split(',')
        if not admin_usernames:
            return
        
        for username in admin_usernames:
            username = username.strip()
            if not username:
                continue
                
            admin = Admin.query.filter_by(username=username).first()
            if not admin:
                admin = Admin(username=username)
                admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin'))  # 默认密码为admin
                db.session.add(admin)
        
        db.session.commit()
