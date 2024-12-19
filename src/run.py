#!/usr/bin/env python3
import os
import sys
import logging
import uvicorn
from logging.handlers import RotatingFileHandler
from app import app, db, asgi_app

def setup_logging():
    """配置日志系统"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        'logs/scores.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('DoScores 启动')

def init_db():
    """初始化数据库"""
    try:
        with app.app_context():
            db.create_all()
            app.logger.info("数据库初始化完成")
    except Exception as e:
        app.logger.error(f"数据库初始化失败: {str(e)}")
        sys.exit(1)

def main():
    """主函数"""
    try:
        # 确保必要的目录存在
        for directory in ['instance', 'logs']:
            if not os.path.exists(directory):
                os.makedirs(directory)
                app.logger.info(f"创建目录: {directory}")
        
        # 设置日志
        setup_logging()
        
        # 初始化数据库
        init_db()
        
        # 运行应用
        port = int(os.getenv('PORT', 8181))
        debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        
        app.logger.info(f"启动服务器于 http://localhost:{port}")
        uvicorn.run(
            asgi_app,
            host='0.0.0.0',
            port=port,
            log_level='debug' if debug else 'info'
        )
        
    except Exception as e:
        app.logger.error(f"应用启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
