from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask import redirect, url_for, current_app
from flask_login import current_user
import os

class SecureModelView(ModelView):
    form_base_class = SecureForm
    
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        return current_user.username == os.getenv('ADMIN_USERNAME')
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('index'))

class SecureAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.username != os.getenv('ADMIN_USERNAME'):
            return redirect(url_for('index'))
        return super().index()

class UserAdmin(SecureModelView):
    column_list = ('username', 'name', 'trust_level', 'original_score', 'actual_score', 'last_updated')
    column_searchable_list = ('username', 'name')
    column_filters = ('trust_level', 'original_score', 'actual_score')
    form_excluded_columns = ('consumptions', 'transfers_sent', 'transfers_received')
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.last_updated = model.created_at
        super().on_model_change(form, model, is_created)

class AppAdmin(SecureModelView):
    column_list = ('name', 'owner.username', 'client_id', 'redirect_uri', 'created_at')
    column_searchable_list = ('name', 'client_id')
    column_filters = ('created_at',)
    form_excluded_columns = ('consumptions',)
    
    def on_model_change(self, form, model, is_created):
        if is_created and not model.client_secret:
            model.client_id = os.urandom(16).hex()
            model.client_secret = os.urandom(32).hex()
        super().on_model_change(form, model, is_created)

class ConsumptionAdmin(SecureModelView):
    column_list = ('user.username', 'app.name', 'amount', 'purpose', 'status', 'created_at', 'confirmed_at')
    column_searchable_list = ('purpose',)
    column_filters = ('status', 'created_at', 'confirmed_at')
    form_excluded_columns = ('confirm_token',)

class TransferAdmin(SecureModelView):
    column_list = ('from_user.username', 'to_user.username', 'amount', 'message', 'status', 'created_at', 'confirmed_at')
    column_searchable_list = ('message',)
    column_filters = ('status', 'created_at', 'confirmed_at')
    form_excluded_columns = ('confirm_token',)

def init_admin(app, db):
    from models.models import User, App, ScoreConsumption, ScoreTransfer
    
    admin = Admin(
        app,
        name='点数系统管理',
        template_mode='bootstrap4',
        index_view=SecureAdminIndexView(),
        base_template='admin/master.html'
    )
    
    admin.add_view(UserAdmin(User, db.session, name='用户管理'))
    admin.add_view(AppAdmin(App, db.session, name='应用管理'))
    admin.add_view(ConsumptionAdmin(ScoreConsumption, db.session, name='消耗记录'))
    admin.add_view(TransferAdmin(ScoreTransfer, db.session, name='转账记录'))
    
    return admin
