# AGENTS.md - 星辰协同平台

## 项目概述

星辰协同平台是一个基于 Django 6.0 的轻量级协同办公系统，聚焦三个核心功能：登录注册、即时通讯和 AI 智能助手。项目从完整版星辰协同平台中提取精简而来。

## 核心架构

### 技术选型

- **后端**: Django 6.0 + Channels 4.1 + Daphne 4.1
- **数据库**: MySQL 8.0（通过 PyMySQL 连接）
- **缓存层**: Redis（Channels channel layer + 缓存）
- **实时通信**: WebSocket（Django Channels consumer）
- **AI 接口**: Dify Workflow API（httpx 异步 HTTP 客户端）
- **前端**: Django Templates + AdminLTE 3 + Bootstrap 5.3

### 模块划分

| 模块 | 路径 | 职责 |
|------|------|------|
| members | `myapp/members/` | 用户认证、个人资料、通知 |
| chat | `myapp/chat/` | 会话管理、消息收发、WebSocket |
| 核心 | `myapp/` | 项目配置、路由、AI 机器人、公告 |

### 数据模型

- **User**（members）— 继承 AbstractUser，扩展 display_name、avatar_url、online_status、phone、organization
- **Organization**（members）— 机构名称、描述
- **Notification**（members）— 通知类型（7类）、已读状态、关联跳转
- **Conversation**（chat）— 会话类型（私聊/群聊）、参与者、归档状态
- **Message**（chat）— 消息内容、附件、撤回状态、已读状态
- **ConversationReadState**（chat）— 用户会话已读时间戳
- **ConversationMember**（chat）— 会话成员角色

### 关键设计决策

1. **Session 认证** — 使用 Django 内置 Session 认证，支持"记住我"（30天过期）
2. **ASGI 双协议** — Daphne 同时处理 HTTP 和 WebSocket，通过 Channels routing 分发
3. **Auth backend** — PhoneOrUsernameModelBackend 支持用户名或手机号登录
4. **通知系统** — WebSocket 消费者实时推送 + HTTP 轮询回退（60s间隔）
5. **AI 机器人** — 群聊中检测 @星辰AI助手，收集最近20条消息作为上下文，调用 Dify API 异步回复
6. **Feature extraction** — 从完整版项目中提取，移除了 events、friends、profile、tasks、tags、calendar 等模块

### WebSocket 路由

```
/ws/chat/{conversation_id}/   → ChatConsumer（消息收发）
/ws/notifications/            → NotificationConsumer（实时通知推送）
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DB_NAME | 数据库名 | xingchen_db |
| DB_USER | 数据库用户 | root |
| DB_PASSWORD | 数据库密码 | xingchen123 |
| DB_HOST | 数据库主机 | 127.0.0.1 |
| DB_PORT | 数据库端口 | 3306 |
| REDIS_URL | Redis 连接 | redis://127.0.0.1:6379/1 |
| AI_API_KEY | Dify API 密钥 | （空） |
| AI_API_BASE_URL | Dify API 地址 | https://api.dify.ai/v1/workflows/run |
| AI_USE_REAL_API | 启用真实 AI | False |
| DJANGO_SECRET_KEY | Django 密钥 | （自动生成） |
| DJANGO_DEBUG | Debug 模式 | True |

## 开发指南

### 启动方式

```bash
# ASGI 模式（支持 WebSocket）
daphne -b 0.0.0.0 -p 8000 myapp.asgi:application

# 或传统 WSGI 模式（不支持 WebSocket）
python manage.py runserver 0.0.0.0:8000
```

### 新增 API 步骤

1. 在对应模块的 `views.py` 中实现视图函数
2. 在模块的 `urls.py` 中注册路由
3. （可选）如果涉及 WebSocket 通知，在 `notify.py` 中添加通知函数

### 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 代码规范

- Python: PEP 8
- 遵循 Django 最佳实践（Fat models, thin views）
- API 返回 JSON 格式（JsonResponse）
- 登录保护使用 `@login_required` 装饰器
- CSRF 豁免使用 `@csrf_exempt`（API 端点）
