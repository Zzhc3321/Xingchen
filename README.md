# 星辰协同平台

基于 Django 6.0 的轻量级协同办公平台，提供登录注册、即时通讯和 AI 智能助手功能。

## 功能特性

- **用户认证** — 登录、注册、个人信息管理、头像上传
- **即时通讯** — 私聊、群聊、消息撤回（2分钟内）、文件/图片发送、消息搜索
- **AI 智能助手** — 群聊中 @星辰AI助手 触发 AI 回复，基于 Dify 工作流 API
- **实时通知** — WebSocket 实时推送通知（新消息、建群、群邀请等）
- **通知公告** — 系统公告管理

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | Django 6.0 |
| 数据库 | MySQL 8.0 |
| 缓存/Channel | Redis + Django Channels 4.1 |
| ASGI 服务 | Daphne 4.1 |
| 实时通信 | WebSocket (Channels) |
| AI 接口 | Dify Workflow API |
| 前端 UI | AdminLTE 3 + Bootstrap 5.3 |
| 认证方式 | Session 认证 |

## 环境要求

- Python >= 3.10
- MySQL 8.0
- Redis (用于 Channels 和缓存)
- 可选的 Dify API 密钥 (用于 AI 助手功能)

## 快速启动

### 1. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置以下内容：
# - MySQL 数据库连接信息
# - Redis 连接信息
# - Dify API 密钥（可选）
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库迁移

```bash
python manage.py migrate
```

### 4. 创建示例数据（可选）

```bash
python manage.py init_demo
```

### 5. 启动服务

```bash
# 使用 Daphne (ASGI，支持 WebSocket)
daphne -b 0.0.0.0 -p 8000 myapp.asgi:application
```

### 6. 访问

打开浏览器访问 `http://localhost:8000`

## 核心接口

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register/` | 用户注册 |
| POST | `/api/auth/login/` | 用户登录 |
| POST | `/api/auth/logout/` | 退出登录 |
| GET | `/api/auth/me/` | 获取当前用户信息 |

### 个人信息

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/profile/update/` | 更新个人资料 |
| POST | `/api/profile/status/` | 更新在线状态 |
| POST | `/api/profile/password/` | 修改密码 |
| POST | `/api/profile/avatar/` | 上传头像 |

### 即时通讯

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/conversations/` | 会话列表 |
| POST | `/api/conversations/create/` | 创建会话 |
| GET | `/api/conversations/<id>/messages/` | 获取消息 |
| POST | `/api/conversations/<id>/send/` | 发送消息 |
| POST | `/api/conversations/<id>/read/` | 标记已读 |
| POST | `/api/conversations/<id>/archive/` | 归档会话 |
| POST | `/api/conversations/<id>/restore/` | 恢复会话 |
| POST | `/api/conversations/<id>/delete/` | 删除会话 |
| POST | `/api/conversations/<id>/messages/<msg_id>/revoke/` | 撤回消息 |
| POST | `/api/conversations/<id>/members/` | 成员管理(邀请/移除) |
| POST | `/api/search/` | 搜索用户和消息 |

### 通知

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/notifications/` | 通知列表 |
| POST | `/api/notifications/read/` | 标记已读 |
| POST | `/api/notifications/<id>/dismiss/` | 忽略通知 |

### 公告

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/announcements/` | 获取公告列表 |

## 测试核心接口

使用 curl 测试：

```bash
# 注册
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123456", "display_name": "测试用户"}'

# 登录
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123456"}' \
  -c cookies.txt

# 获取当前用户
curl http://localhost:8000/api/auth/me/ -b cookies.txt

# 获取会话列表
curl http://localhost:8000/api/conversations/ -b cookies.txt

# 发送消息
curl -X POST http://localhost:8000/api/conversations/1/send/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"content": "你好！"}'
```

## AI 助手

在群聊中发送包含 `@星辰AI助手` 的消息即可触发 AI 回复。需要配置 Dify API：

- `AI_API_KEY` — Dify Workflow API 密钥
- `AI_API_BASE_URL` — Dify API 地址（可选，有默认值）
- `AI_USE_REAL_API` — 设为 `True` 启用真实 API（默认使用模拟回复）

## 项目目录结构

```
myapp/
├── asgi.py              # ASGI 配置（WebSocket 路由）
├── settings.py          # Django 项目配置
├── urls.py              # 主路由
├── views.py             # 页面视图
├── models.py            # 公告模型
├── notify.py            # 通知工具函数
├── ai_robot.py          # AI 机器人接口
├── members/             # 用户模块
│   ├── models.py        # 用户、机构、通知模型
│   ├── views.py         # 认证、个人资料、通知 API
│   ├── urls.py          # 路由
│   ├── admin.py         # 后台管理
│   └── consumers.py     # WebSocket 通知消费者
├── chat/                # 通讯模块
│   ├── models.py        # 会话、消息模型
│   ├── views.py         # 通讯 API
│   ├── urls.py          # 路由
│   ├── consumers.py     # WebSocket 聊天消费者
│   └── management/      # 管理命令
└── templates/           # 页面模板
    ├── base.html        # 基础布局
    ├── login.html       # 登录页
    ├── register.html    # 注册页
    ├── dashboard.html   # 工作台
    └── chat.html        # 即时通讯页
```

## 部署

推荐使用 Daphne 作为 ASGI 服务器：

```bash
pip install daphne
daphne -b 0.0.0.0 -p 8000 myapp.asgi:application
```

生产环境建议：
- 使用 Nginx 反向代理
- 配置 SSL 证书
- 使用 Supervisor 或 systemd 管理进程
- 配置 MySQL 主从或备份策略
- 配置 Redis 持久化
