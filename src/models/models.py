from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer, unique=True)
    username = db.Column(db.String(80), unique=True)
    name = db.Column(db.String(120))
    trust_level = db.Column(db.Integer)
    original_score = db.Column(db.Integer, default=0)  # 原始点数
    actual_score = db.Column(db.Integer, default=0)    # 实际点数
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    apps = db.relationship('App', backref='owner', lazy=True)
    consumptions = db.relationship('ScoreConsumption', backref='user', lazy=True)
    
    # Flask-Login接口要求
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def consumed_score(self):
        """获取已消耗的点数"""
        return self.original_score - self.actual_score

class App(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    client_id = db.Column(db.String(64), unique=True, nullable=False)
    client_secret = db.Column(db.String(64), unique=True, nullable=False)
    redirect_uri = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<App {self.name}>'

class ScoreConsumption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    app_id = db.Column(db.Integer, db.ForeignKey('app.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.String(256))
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, rejected
    confirm_token = db.Column(db.String(64), unique=True)
    confirmed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    app = db.relationship('App', backref='consumptions', lazy=True)
    
    def __repr__(self):
        return f'<ScoreConsumption {self.id}>'

class ScoreTransfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(256))
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, rejected
    confirm_token = db.Column(db.String(64), unique=True)
    confirmed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='transfers_sent')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='transfers_received')
    
    def __repr__(self):
        return f'<ScoreTransfer {self.id}>'
