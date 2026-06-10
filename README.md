# Xingchen — 团队协作平台

基于 Django 6.0 的企业级团队协作系统，集成即时通讯、事件管理、任务派单和成员管理，支持 WebSocket 实时推送。

## 功能

**即时通讯**
- 私聊与群聊，WebSocket 实时消息推送
- 消息附件上传、已读状态追踪、消息撤回
- 会话已读状态管理

**事件管理**
- 事件全生命周期（售前/售中/售后/自定义分类）
- 优先级、标签、参与人、联系人信息
- 日历备忘，事件关联群聊自动建群

**成员系统**
- 自定义用户模型（显示名、头像、在线状态）
- 好友添加/搜索，组织架构管理
- 通知中心（7 类通知：好友申请、消息、群聊邀请、任务派单等）

**任务派单**
- 任务创建、分配、状态流转（待处理→进行中→已完成）
- 附件支持，全文描述

## 技术栈

| 层 | 技术 |
|---|---|
| 框架 | Django 6.0.5 |
| ASGI 服务 | Daphne 4.1 + Django Channels 4.1 |
| 实时通信 | WebSocket (channel layer) |
| API | Django REST Framework 3.16 |
| 数据库 | MySQL (PyMySQL) |
| 前端 | Django Templates + SimpleUI |

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python manage.py migrate

# 导入演示数据
python manage.py init_demo

# 启动服务 (ASGI — 支持 WebSocket)
daphne -b 0.0.0.0 -p 8089 myapp.asgi:application
```

一键启动：

```bash
bash scripts/start.sh
```

## 项目结构

```
myapp/
├── chat/          # 即时通讯模块（models + consumers + routing）
├── events/        # 事件管理模块（含日历备忘、事件群组）
├── members/       # 成员系统（用户/好友/组织/标签/任务/通知）
├── templates/     # 前端页面（登录/注册/面板/聊天/好友/事件/个人）
├── static/        # 静态资源
├── settings.py    # Django 配置
├── urls.py        # 路由配置
├── asgi.py        # ASGI 入口（WebSocket）
├── ai_robot.py    # 机器人模块
└── notify.py      # 实时通知推送
```

## 路由

| 路径 | 页面 |
|---|---|
| `/` | 登录 |
| `/auth/register/` | 注册 |
| `/dashboard/` | 工作台 |
| `/chat/` | 即时通讯 |
| `/friends/` | 好友管理 |
| `/events/` | 事件管理 |
| `/profile/` | 个人设置 |
| `/api/*` | REST API 端点 |
| `/admin/` | 管理后台 |

## 环境要求

- Python ≥ 3.11
- MySQL 8.0+
- Redis（可选，用于 channel layer 生产部署）
