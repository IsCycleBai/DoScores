# 点数消耗系统

基于论坛信任等级的通用积分系统，支持应用接入和点数转账。

## 功能特性

- 论坛OAuth2认证
- 点数消耗和转账
- 开发者应用管理
- API接口和在线调试
- 操作确认机制
- 响应式界面
- 亮暗主题切换

## 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/scores.git
cd scores
```

2. 创建虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp src/.env.example src/.env
```

编辑 `src/.env` 文件，填入必要的配置：
```ini
FLASK_SECRET_KEY=your-secret-key
FLASK_DEBUG=True
DATABASE_URL=sqlite:///scores.db

# OAuth2配置
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=http://localhost:8181/oauth2/callback

# ZenRows代理配置（可选，仅在遇到403错误时使用）
ZENROWS_PROXY=your-zenrows-proxy-url
```

5. 运行应用
```bash
cd src
python run.py
```

访问 http://localhost:8181 开始使用。

## 开发者接入

1. 使用论坛账号登录系统
2. 进入开发者中心创建应用
3. 获取 client_id 和 client_secret
4. 使用API请求消耗点数

### API示例

```python
import requests

# 请求消耗点数
response = requests.post(
    'http://localhost:8181/api/score/consume',
    headers={
        'Authorization': 'your-client-id:your-client-secret',
        'Content-Type': 'application/json'
    },
    json={
        'username': 'example_user',
        'amount': 10,
        'purpose': '购买服务'
    }
)

# 获取确认URL
data = response.json()
if data['success']:
    confirm_url = data['confirm_url']
    # 在新窗口中打开确认URL
    # window.open(confirm_url + '?popup=1', 'confirm', 'width=600,height=600')
```

### 确认流程

1. API返回确认URL
2. 在新窗口中打开确认URL
3. 用户确认或拒绝操作
4. 接收确认结果
```javascript
window.addEventListener('message', function(event) {
    if (event.data.success) {
        console.log('操作成功', event.data);
    } else {
        console.error('操作失败', event.data.error);
    }
});
```

## 在线调试

系统提供API Playground功能，可以在线测试API接口：

1. 登录系统
2. 进入开发者中心
3. 点击"API Playground"
4. 选择应用并填写参数
5. 发送请求并查看响应

## 目录结构

```
scores/
├── src/
│   ├── api/            # API接口
│   ├── models/         # 数据模型
│   ├── templates/      # 页面模板
│   ├── static/         # 静态文件
│   ├── .env           # 环境配置
│   ├── app.py         # 主应用
│   └── run.py         # 启动脚本
├── requirements.txt    # 项目依赖
└── README.md          # 项目说明
```

## 技术栈

- Python 3.12+
- Flask + ASGI
- SQLAlchemy
- Authlib
- Tailwind CSS
- SQLite

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

[MIT](LICENSE)
