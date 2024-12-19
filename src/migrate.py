from app import app, db
from flask_migrate import Migrate
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info("初始化 Flask-Migrate...")
    migrate = Migrate(app, db)

    with app.app_context():
        logger.info("创建数据库...")
        db.create_all()
        
        logger.info("执行数据库迁移...")
        from flask_migrate import upgrade
        upgrade()
        
        logger.info("数据库迁移完成!")
except Exception as e:
    logger.error(f"迁移过程中出错: {str(e)}")
    raise
