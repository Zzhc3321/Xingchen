"""Seed realistic demo data for all pages — events, tasks, memos, materials, etc."""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from myapp.members.models import User, Organization, Task, Notification
from myapp.events.models import Event, CalendarMemo
from myapp.models import Announcement, SavedReport


REAL_USERS = [
    {"name": "张明远", "org": "技术研发部", "bio": "全栈工程师，热爱开源"},
    {"name": "李思涵", "org": "产品设计部", "bio": "产品经理，专注用户体验"},
    {"name": "王浩然", "org": "市场营销部", "bio": "市场总监，10年行业经验"},
    {"name": "陈雨桐", "org": "客户成功部", "bio": "客户成功经理"},
    {"name": "刘子轩", "org": "技术研发部", "bio": "后端开发工程师"},
    {"name": "赵雪晴", "org": "人力资源部", "bio": "HRBP，关注团队成长"},
    {"name": "孙博文", "org": "财务部", "bio": "财务分析师"},
    {"name": "周若汐", "org": "产品设计部", "bio": "UI/UX 设计师"},
    {"name": "吴昊天", "org": "市场营销部", "bio": "品牌运营专员"},
    {"name": "郑雅文", "org": "客户成功部", "bio": "售后技术支持"},
]

TASK_SEEDS = [
    ("完成用户管理模块的单元测试", "对用户管理模块的增删改查接口编写完整的单元测试，要求覆盖率 ≥ 85%", "in_progress"),
    ("修复支付回调超时问题", "生产环境反馈支付回调偶发超时，需要排查第三方接口响应慢的原因并优化", "in_progress"),
    ("撰写季度产品复盘报告", "汇总 Q2 产品数据，包括用户增长、功能使用率、留存等核心指标", "pending"),
    ("设计新版本登录页 UI", "配合品牌升级，重新设计登录页面，要求简洁现代风格", "pending"),
    ("优化数据库查询性能", "对慢查询日志中 TOP 10 的 SQL 进行索引优化和执行计划分析", "in_progress"),
    ("安排下周一团队建设活动", "预算 3000 元以内，需统计人数并预订场地", "pending"),
    ("更新 API 文档", "RESTful API 接口文档需要补充最新新增的三个接口的说明和示例", "completed"),
    ("客户满意度调研分析", "回收 200 份调研问卷，输出满意度分析报告和改进建议", "completed"),
    ("配置 CI/CD 流水线", "使用 GitHub Actions 配置自动化构建、测试和部署流水线", "completed"),
    ("准备周会汇报材料", "汇总本周工作进展、遇到的问题和下周计划", "pending"),
    ("处理客户退款申请", "客户反馈商品与描述不符，核实后执行退款流程", "in_progress"),
    ("编写新员工入职培训手册", "整理技术栈、开发流程和常用工具的使用说明", "pending"),
    ("研究 AI 代码助手接入方案", "调研 Claude Code、GitHub Copilot 等工具的团队使用方案", "pending"),
    ("修复移动端适配问题", "个人中心页面在 iPhone SE 上布局错位，需要修复", "in_progress"),
    ("完成 6 月份财务对账", "核对 6 月份收支明细，输出对账报告", "completed"),
    ("搭建内部知识库系统", "基于 Confluence 搭建团队知识库，整理已有文档迁移", "in_progress"),
    ("开展用户访谈", "邀请 5 名核心用户进行深度访谈，收集产品改进建议", "pending"),
    ("优化系统登录页加载速度", "首屏加载时间从 3.2s 优化到 1s 以内", "completed"),
    ("处理安全漏洞扫描报告", "修复扫描报告中的 3 个高危漏洞和 5 个中危漏洞", "in_progress"),
    ("设计促销活动方案", "618 大促活动页面和优惠策略设计方案", "pending"),
]

EVENT_SEEDS = {
    "pre_sales": [
        ("智慧园区项目前期沟通", "与华远科技初步沟通智慧园区解决方案需求", "高"),
        ("金融客户方案评审", "招商银行私有云部署方案内部评审", "高"),
        ("教育行业客户拜访", "复旦大学信息化建设需求对接", "中"),
        ("电商平台技术选型", "帮助某头部电商评估技术方案", "中"),
        ("制造业数字化转型方案", "为三一重工提供数字化转型咨询", "低"),
    ],
    "in_sales": [
        ("政务云平台项目实施", "市级政务云平台部署实施，周期 3 个月", "高"),
        ("ERP 系统迁移项目", "某制造企业从旧系统迁移至新 ERP", "高"),
        ("数据中台建设", "零售企业数据中台一期建设", "中"),
        ("APP 性能优化项目", "客户 APP 崩溃率从 1.2% 优化至 0.3%", "中"),
        ("官网改版项目", "集团公司官网全面改版升级", "低"),
    ],
    "after_sales": [
        ("生产环境故障排查", "客户生产环境出现服务不可用，紧急排查", "高"),
        ("季度系统巡检", "为客户进行季度系统巡检和健康检查", "中"),
        ("版本升级支持", "协助客户从 v2.1 升级到 v3.0", "中"),
        ("数据迁移技术支持", "帮助客户将历史数据迁移至新系统", "低"),
        ("培训服务交付", "为客户团队提供为期 3 天的使用培训", "低"),
    ],
    "custom": [
        ("团队技术分享会", "每周五下午内部技术分享交流", "中"),
        ("年度合作伙伴大会", "邀请合作伙伴参加年度大会", "低"),
        ("新人入职培训", "本月新入职 3 位同事的培训安排", "中"),
        ("代码审查会议", "对本周合并的 PR 进行集中审查", "低"),
        ("季度 OKR 制定会", "下个季度目标和关键结果制定", "高"),
    ],
}

ANNOUNCEMENTS = [
    {"title": "关于 2026 年端午节放假安排的通知", "content": "根据国家法定节假日规定，端午节放假安排如下：6 月 25 日至 6 月 27 日放假共 3 天，请各部门做好节前安全检查。", "pinned": True},
    {"title": "公司新系统上线通知", "content": "经过三个月的开发和测试，新版协同管理系统将于 6 月 15 日正式上线，新版本增加了事件管理、任务派单等功能模块。", "pinned": True},
    {"title": "2026 年第二季度团建活动报名", "content": "二季度团建活动定于 6 月 20 日在西山森林公园举行，请各部门在 6 月 10 日前提交参加人员名单。", "pinned": False},
    {"title": "本月优秀员工表彰", "content": "经评选，张明远、李思涵、王浩然三位同事被评为本月优秀员工，感谢他们的杰出贡献！", "pinned": False},
    {"title": "办公室搬迁通知", "content": "因业务扩展，公司将于 7 月 1 日搬迁至朝阳区科技园 B 座 15 层，IT 部门将协助完成工位网络配置。", "pinned": False},
    {"title": "2026 年度技术大会报名", "content": "年度技术大会将于 8 月 15-16 日举行，欢迎各部门踊跃报名参加技术分享和展示。", "pinned": False},
    {"title": "关于规范使用协同平台的通知", "content": "请各部门确保所有事件和任务在系统中及时更新状态，平台使用情况将纳入季度考核。", "pinned": False},
]

MAT_SEEDS = [
    ("daily", "日报", "今日工作内容：\n1. 完成了核心模块的开发任务\n2. 修复了 2 个线上 Bug\n3. 参加了项目进度会议\n\n明日计划：\n- 继续推进功能开发\n- 代码审查待合并的 PR"),
    ("daily", "日报", "今日工作内容：\n1. 处理了客户反馈的 3 个问题\n2. 与产品团队沟通新需求\n3. 编写技术文档\n\n遇到的问题：\n- 第三方接口响应不稳定，已联系技术支持"),
    ("weekly", "周报", "## 本周工作\n\n### 重点工作\n- 完成模块重构\n- 修复线上 Bug\n- 性能优化\n\n### 下周计划\n- 版本发布准备\n- 数据库优化方案设计"),
    ("user_doc", "工作笔记", "## 常用命令\n\n### Git\n```\ngit commit -m \"feat: ...\"\ngit push origin main\n```\n\n### 部署\n```\ndaphne -b 0.0.0.0 -p 8089 myapp.asgi:application\n```"),
    ("user_doc", "项目规范", "## 命名规范\n- 类名: PascalCase\n- 函数/变量: snake_case\n- 常量: UPPER_SNAKE_CASE\n\n## 提交规范\nfeat/fix/chore/refactor: 描述"),
    ("archive_summary", "群聊总结", "会议讨论要点：\n\n1. 项目进度正常\n2. 接口文档需要补充\n3. 下周确认发布日期\n\n待办：\n- 补充 API 文档\n- 确认 UI 评审时间"),
]

MEMO_SEEDS = [
    ("项目评审会", "10:00 召集各技术负责人进行架构评审"),
    ("客户电话会议", "14:30 与客户沟通需求变更"),
    ("提交周报", "下班前提交本周工作周报"),
    ("团队站会", "09:30 每日站会，同步进展"),
    ("代码 Review", "审查待合并的 PR"),
    ("版本发布", "v3.2.0 版本发布，注意回滚方案"),
    ("财务报销", "提交上月差旅费用报销单据"),
    ("面试候选人", "14:00 面试候选人"),
]


def _pick_days_ago(days_min=0, days_max=60):
    return timezone.now() - timedelta(days=random.randint(days_min, days_max))


class Command(BaseCommand):
    help = "为所有页面元素填充逼真的演示数据"

    def handle(self, *args, **options):
        self.stdout.write("填充演示数据...\n")

        # ── Orgs ──
        org_names = ["技术研发部", "产品设计部", "市场营销部", "客户成功部", "人力资源部", "财务部"]
        for name in org_names:
            Organization.objects.get_or_create(name=name, defaults={"description": f"{name}"})
        self.stdout.write("  [✓] 机构已就绪")

        # ── Users ──
        users_created = 0
        for info in REAL_USERS:
            phone = f"1{random.randint(30, 99)}{random.randint(10000000, 99999999)}"
            user, created = User.objects.get_or_create(
                username=info["name"],
                defaults={
                    "display_name": info["name"],
                    "phone": phone,
                    "bio": info["bio"],
                    "organization": Organization.objects.filter(name=info["org"]).first(),
                    "online_status": random.choice(["online", "away", "dnd", "offline"]),
                },
            )
            if created:
                user.set_password("123456")
                user.save()
                users_created += 1
        self.stdout.write(f"  [✓] 用户已就绪（新增 {users_created}）")

        demo_users = User.objects.filter(username__in=[u["name"] for u in REAL_USERS])
        all_users = User.objects.filter(is_active=True)

        # ── Announcements ──
        for a in ANNOUNCEMENTS:
            Announcement.objects.get_or_create(
                title=a["title"],
                defaults={"content": a["content"], "is_pinned": a["pinned"], "created_at": _pick_days_ago(1, 90)},
            )
        self.stdout.write(f"  [✓] 公告已就绪（{Announcement.objects.count()} 条）")

        # ── Events ──
        ev_count = Event.objects.count()
        if ev_count < 25:
            need = 30 - ev_count
            created = 0
            attempts = 0
            while created < need and attempts < 200:
                attempts += 1
                cat = random.choice(list(EVENT_SEEDS.keys()))
                title_template, desc, pri = random.choice(EVENT_SEEDS[cat])
                if Event.objects.filter(title=title_template).exists():
                    continue
                ev_date = _pick_days_ago(0, 60)
                Event.objects.create(
                    title=title_template, description=desc, category=cat,
                    priority={"高": "high", "中": "medium", "低": "low"}[pri],
                    status=random.choice(["open", "in_progress", "closed"]),
                    start_date=(ev_date - timedelta(days=random.randint(0, 5))).date(),
                    end_date=(ev_date + timedelta(days=random.randint(1, 14))).date(),
                    contact_person=random.choice(REAL_USERS)["name"],
                    contact_phone=f"1{random.randint(30, 99)}{random.randint(10000000, 99999999)}",
                    created_by=random.choice(list(demo_users)),
                    created_at=ev_date, updated_at=ev_date + timedelta(hours=random.randint(1, 72)),
                )
                created += 1
        self.stdout.write(f"  [✓] 事件已就绪（{Event.objects.count()} 条）")

        # ── Tasks — 每个用户至少 2 条 ──
        all_assignees = list(all_users)
        for user in demo_users:
            existing = Task.objects.filter(assignee=user).exclude(status__in=["completed", "cancelled"]).count()
            for _ in range(max(0, 3 - existing)):
                title, desc, status = random.choice(TASK_SEEDS)
                Task.objects.create(
                    title=title, description=desc, status=status,
                    created_by=random.choice(all_assignees), assignee=user,
                    created_at=_pick_days_ago(0, 30),
                )
        self.stdout.write(f"  [✓] 任务已就绪（{Task.objects.count()} 条）")

        # ── Calendar Memos — 每个用户 3-5 条 ──
        for user in demo_users:
            existing = CalendarMemo.objects.filter(user=user).count()
            for _ in range(max(0, 4 - existing)):
                title, content = random.choice(MEMO_SEEDS)
                CalendarMemo.objects.create(
                    user=user, date=timezone.now().date() + timedelta(days=random.randint(-7, 14)),
                    title=title, content=content,
                )
        self.stdout.write(f"  [✓] 日历备忘已就绪（{CalendarMemo.objects.count()} 条）")

        # ── Materials — 每个用户 3-5 条 ──
        for user in demo_users:
            existing = SavedReport.objects.filter(user=user).count()
            for _ in range(max(0, 4 - existing)):
                rtype, prefix, content = random.choice(MAT_SEEDS)
                title = f"{prefix} {_pick_days_ago(0, 30).strftime('%m-%d')}"
                SavedReport.objects.create(
                    user=user, title=title, report_type=rtype, content=content,
                    source=random.choice(["report_generator", "user_save"]),
                    created_at=_pick_days_ago(0, 30),
                    is_pinned=random.random() < 0.15,
                )
        self.stdout.write(f"  [✓] 材料已就绪（{SavedReport.objects.count()} 条）")

        # ── Summary ──
        self.stdout.write("\n✅ 演示数据填充完成！")
        self.stdout.write(f"   用户: {User.objects.count()}")
        self.stdout.write(f"   事件: {Event.objects.count()}")
        self.stdout.write(f"   任务: {Task.objects.count()}")
        self.stdout.write(f"   公告: {Announcement.objects.count()}")
        self.stdout.write(f"   备忘: {CalendarMemo.objects.count()}")
        self.stdout.write(f"   材料: {SavedReport.objects.count()}")
        self.stdout.write(f"   通知: {Notification.objects.count()}")

        self.stdout.write("\n演示用户登录密码均为: 123456")
        for u in demo_users:
            t = Task.objects.filter(assignee=u).exclude(status__in=["completed", "cancelled"]).count()
            m = SavedReport.objects.filter(user=u).count()
            c = CalendarMemo.objects.filter(user=u).count()
            self.stdout.write(f"   {u.display_name} [{u.organization or '无部门'}]: 任务={t} 材料={m} 备忘={c}")
