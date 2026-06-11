"""为每个已有用户、每个页面元素补充逼真的电信业务演示数据（全量替换）"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from myapp.members.models import User, Task, Notification
from myapp.models import SavedReport
from myapp.events.models import Event, CalendarMemo


# ── 电信业务数据池（全部为电信业务内容）──

TASK_TITLES = [
    ("处理宽带装维工单", "FTTH 用户报装，需在 24 小时内完成入户安装调试", "in_progress"),
    ("光缆线路巡检", "对辖区内 3 条主干光缆进行例行巡检，排查隐患", "in_progress"),
    ("5G 基站开通测试", "新站点的 5G NR 设备开通入网测试", "in_progress"),
    ("政企专线故障处理", "某政企客户 OTN 专线中断，需紧急排查处理", "in_progress"),
    ("核心网设备升级", "EPC 核心网网元软件版本升级，需凌晨割接", "pending"),
    ("用户投诉处理", "用户反馈宽带速率不达标，安排上门测速", "in_progress"),
    ("IPRAN 链路扩容", "城域网 IPRAN 链路带宽利用率超 80%，需扩容", "pending"),
    ("家客装维满意度回访", "对本月新装宽带用户进行满意度回访", "pending"),
    ("传输网管告警清理", "处理传输网管系统上的存量告警", "in_progress"),
    ("政企客户走访", "拜访辖区内重点政企客户，了解业务需求", "pending"),
    ("云计算资源池扩容", "天翼云资源池服务器上架和网络配置", "in_progress"),
    ("IDC 机房巡检", "检查 IDC 机房温湿度、电力、消防设施", "completed"),
    ("物联网卡激活处理", "处理批量物联网卡激活工单", "in_progress"),
    ("智慧社区项目交付", "某智慧社区门禁、监控系统安装调试", "in_progress"),
    ("天翼看家安装", "用户办理天翼看家业务，上门安装摄像头", "pending"),
    ("新装电话业务开通", "用户申请固定电话新装，跳线及数据制作", "pending"),
    ("大客户电路开通", "某银行点对点 100M 电路开通及测试", "in_progress"),
    ("OLT 设备割接", "老旧 OLT 设备替换割接，影响 500 户", "pending"),
    ("无线网优测试", "重点区域 4G/5G 信号覆盖测试和优化", "in_progress"),
    ("政企云业务迁移", "协助客户将业务系统迁移至天翼云", "pending"),
    ("应急通信保障", "重大活动应急通信车开通和现场保障", "completed"),
    ("管线资源清查", "对辖区内管道和杆路资源进行清查录入", "in_progress"),
    ("天翼高清业务调试", "用户办理 IPTV 业务，上门调试机顶盒", "pending"),
    ("VoLTE 质量优化", "VoLTE 语音质量指标优化和参数调整", "in_progress"),
    ("城域网核心节点巡检", "对城域网核心路由器、交换机进行健康检查", "completed"),
    ("政企 ICT 项目验收", "某政企 ICT 项目设备安装调试完成，组织验收", "pending"),
    ("接入网扩容工程", "PON 口利用率超 70%，需要新增板卡扩容", "in_progress"),
    ("通信机房电源检查", "检查各通信机房蓄电池和 UPS 运行状态", "completed"),
    ("天翼云会议保障", "重要视频会议保障，提前测试线路", "pending"),
    ("基站退服故障处理", "某基站因供电故障退服，需发电保障", "in_progress"),
    ("光缆抢修", "主干光缆被施工挖断，需紧急熔纤抢修", "in_progress"),
    ("网络信息安全管理", "对辖区 IP 地址和域名进行安全扫描", "pending"),
    ("欠费用户催缴", "对欠费超过 3 个月的政企客户进行电话催缴", "pending"),
    ("智能家居业务推广", "向存量宽带用户推广全屋 WiFi 智能组网服务", "pending"),
    ("数据专线 SLA 报告", "向 VIP 客户输出月度数据专线 SLA 达标报告", "completed"),
]

MAT_CONTENT = [
    ("daily", "装维日报", "今日装机情况：\n1. FTTH 新装 8 户，全部当日通\n2. 故障处理 5 单，其中光缆故障 2 单\n3. 移机 3 户\n\n明日计划：\n- 继续跟进欠费停机用户的复机\n- 完成 3 户政企专线开通测试"),
    ("daily", "维护日报", "今日维护工作：\n1. 完成 3 个基站的例行巡检\n2. 处理传输告警 12 条\n3. OLT 板卡替换 1 块\n\n遗留问题：\n- XX 机房蓄电池组需要更换\n- 某段落光缆挂牌缺失需补充"),
    ("daily", "客响日报", "今日工作内容：\n1. 处理政企客户投诉 2 起\n2. 新开通政企专线 4 条\n3. 完成某银行电路扩容\n\n明日安排：\n- 跟进某学校智慧校园项目方案\n- 准备政企客户走访材料"),
    ("daily", "网优日报", "今日测试工作：\n1. 完成 5 个区域的 LTE 覆盖测试\n2. 调整天线倾角 3 面\n3. 处理 MR 弱覆盖小区 8 个\n\n明日计划：\n- 5G 簇优化测试\n- 投诉热点区域优化"),
    ("daily", "营业日报", "今日营业情况：\n1. 办理新装宽带 15 户\n2. 融合套餐升级 8 户\n3. 天翼看家 5 户\n\n明日重点：\n- 继续推进 5G 升级包营销\n- 跟进欠费用户复机"),
    ("weekly", "装维周报", "## 本周装维工作\n\n### 完成情况\n- 宽带新装 42 户，装机及时率 100%\n- 故障处理 28 单，平均修复时长 4.5h\n- 移机 15 户\n\n### 存在问题\n- 部分区域资源未覆盖需协调\n- 光缆故障占比偏高\n\n### 下周计划\n- 配合光缆线路整治\n- 加强装维服务规范"),
    ("weekly", "政企周报", "## 本周政企工作\n\n### 完成事项\n- 新签政企专线 6 条\n- 云业务签约 3 单\n- 客户满意度回访完成\n\n### 下周计划\n- 某开发区智慧园区方案提交\n- 跟进在谈的大客户项目"),
    ("weekly", "网运周报", "## 本周网络运行\n\n### 指标情况\n- 全网无重大故障\n- 核心网元可用率 99.99%\n- 传输网误码率达标\n\n### 重点工作\n- 完成 3 次光缆割接\n- 核心路由器软件升级\n\n### 下周计划\n- 启动季度备品备件盘点\n- 防汛通信保障准备"),
    ("user_doc", "光缆熔纤操作规程", "## 光缆熔纤操作规范\n\n### 准备工具\n- 光纤熔接机\n- 光纤切割刀\n- 光功率计\n- 红光笔\n\n### 操作步骤\n1. 开剥光缆外皮\n2. 固定加强芯\n3. 清洗光纤\n4. 切割端面\n5. 熔接\n6. 热缩保护\n7. 盘纤固定"),
    ("user_doc", "宽带装维服务规范", "## 装维服务七步法\n\n1. 预约上门时间\n2. 规范着装上门\n3. 现场施工规范\n4. 业务测试确认\n5. 用户签字确认\n6. 清理施工垃圾\n7. 引导用户评价\n\n### 注意事项\n- 入户必须穿鞋套\n- 布线必须穿管\n- 熔纤盘必须固定"),
    ("user_doc", "5G 基站开通流程", "## 5G NR 基站开通流程\n\n### 准备工作\n- 站点勘察报告\n- 传输链路确认\n- 天馈系统安装\n\n### 开通步骤\n1. 上电自检\n2. 传输通道测试\n3. 网元注册\n4. 邻区配置\n5. 业务测试\n6. 入网确认"),
    ("user_doc", "机房巡检标准", "## 通信机房巡检项目\n\n### 环境检查\n- 温度：18-25℃\n- 湿度：40%-70%\n- 洁净度\n\n### 设备检查\n- 设备指示灯状态\n- 风扇运行声音\n- 线缆标签完整性\n- 接地电阻测试"),
    ("archive_summary", "光缆抢修群聊总结", "本次光缆抢修讨论要点：\n\n1. 故障点位于人民路与建设路交叉口\n2. 影响政企客户 3 户、家客约 200 户\n3. 已安排抢修队伍现场作业\n\n完成情况：\n- 熔纤完成，业务已恢复\n- 需后续补充光缆标识"),
    ("archive_summary", "项目攻坚群聊总结", "智慧园区项目推进会议：\n\n1. 一期设备已全部安装到位\n2. 平台联调已完成 80%\n3. 下周进行系统整体测试\n\n待办事项：\n- 确认验收时间\n- 准备培训材料"),
    ("user_doc", "天翼云操作手册", "## 天翼云常用操作\n\n### 控制台登录\n- 访问天翼云门户\n- 统一认证登录\n\n### 资源管理\n- 云主机创建/释放\n- 带宽升降配\n- 安全组配置\n\n### 故障排查\n- 检查云监控告警\n- 查看操作日志\n- 提工单处理"),
    ("user_doc", "传输网管操作指南", "## 传输网管常用操作\n\n### 告警管理\n- 查看当前告警\n- 告警确认\n- 告警清除\n\n### 性能管理\n- 误码性能查询\n- 光功率查询\n\n### 配置管理\n- 交叉连接配置\n- 业务路径创建"),
]

MEMO_TITLES = [
    ("光缆割接通知", "凌晨 0:00-6:00 进行光缆割接，影响范围见工单"),
    ("政企客户拜访", "10:00 拜访某银行信息中心负责人谈专线业务"),
    ("周例会", "09:00 部门周例会，汇报上周装维指标"),
    ("基站巡检", "安排本周完成 10 个基站的例行巡检"),
    ("装维晨会", "08:30 装维班组晨会，分配当日工单"),
    ("机房巡检", "检查 IDC 机房温湿度和设备运行状态"),
    ("项目验收", "14:00 某 ICT 项目验收会议"),
    ("网络割接准备", "确认今晚割接方案和回退预案"),
    ("客户投诉处理", "回访投诉用户，确认宽带修复情况"),
    ("5G 路测", "09:30 前往测试区域进行 5G 信号路测"),
    ("安全培训", "15:00 参加季度通信安全生产培训"),
    ("资源确认", "确认新装工单的 OLT 端口资源是否充足"),
    ("方案评审", "某智慧校园技术方案内部评审"),
    ("欠费催缴", "整理本月政企欠费清单并电话催缴"),
    ("SLA 报告提交", "向 VIP 客户提交本月网络 SLA 达标报告"),
]

NOTIF_MESSAGES = [
    ("task_assigned", "新装工单待处理", "您有一个新的 FTTH 装机工单，请及时联系用户预约上门时间"),
    ("system", "网络割接通知", "今晚 0:00-6:00 将对城域网核心设备进行升级割接"),
    ("group_archived_with_summary", "抢修群聊总结已生成", "光缆抢修工作总结已生成，请查看详情"),
    ("system", "网管告警通知", "XX 机房传输设备出现告警，请及时处理"),
    ("task_assigned", "故障工单催办", "用户故障申告已超 4 小时未处理，请尽快联系用户"),
    ("system", "版本升级通知", "综合网管系统已升级至 v4.2，请关注功能变化"),
    ("task_assigned", "政企专线开通任务", "新签约政企专线需在 5 个工作日内完成开通"),
    ("system", "巡检提醒", "本月基站巡检任务尚有 3 个站点未完成"),
    ("task_assigned", "光缆抢修任务", "人民路主干光缆被挖断，请立即赶赴现场抢修"),
    ("system", "资源预警", "XX 局 OLT 上联带宽利用率已达 85%，请规划扩容"),
]

# ── 电信业务事件数据 ──

EVENT_SEEDS = {
    "pre_sales": [
        ("某开发区智慧园区咨询", "为某经济技术开发区提供智慧园区整体解决方案咨询，包含 IoT 平台、园区安防、智能照明等子系统", "高"),
        ("某银行专线接入方案", "某国有银行支行需要 50M MSTP 专线接入总行系统，需提供技术方案和报价", "高"),
        ("某学校智慧校园项目", "某职业高中智慧校园建设项目，包括校园网络覆盖、一卡通、安防监控", "中"),
        ("某医院信息化建设", "某三甲医院新院区信息化建设，包含 HIS 系统网络、无线覆盖、数据中心", "高"),
        ("某企业上云需求对接", "某制造企业计划将 ERP 系统迁移至天翼云，进行前期的需求调研", "中"),
        ("某酒店 TV 业务洽谈", "某连锁酒店集团 200 间客房的天翼高清 IPTV 业务合作洽谈", "低"),
        ("工业互联网项目交流", "与某经开区经发局交流 5G+工业互联网典型应用场景", "中"),
        ("某超市连锁组网方案", "某连锁超市 30 个门店需要 SD-WAN 组网，进行方案设计", "低"),
    ],
    "in_sales": [
        ("智慧园区一卡通实施", "某科技园一卡通系统安装调试，包括门禁、消费、停车子系统", "高"),
        ("政企 OTN 专线开通", "某政务中心 100M OTN 专线开通，涉及光路调测和设备配置", "高"),
        ("5G 基站设备安装", "新建 5G NR 基站 3 个站点的华为 AAU 设备安装和天线调整", "高"),
        ("天翼云主机部署", "某电商平台双十一期间天翼云资源扩容和 CDN 加速部署", "中"),
        ("光纤入户工程施工", "某老旧小区 300 户 FTTH 改造工程，敷设入户皮线光缆", "中"),
        ("IPRAN 设备替换", "某汇聚节点 IPRAN 设备老旧替换，涉及业务割接", "中"),
        ("某视频监控项目", "某街道办雪亮工程视频监控 50 个点位安装调试", "中"),
        ("数据专线提速", "某证券公司数据专线从 10M 提速至 50M，光路调整", "低"),
    ],
    "after_sales": [
        ("政企专线中断紧急处理", "某银行 OTN 专线中断，影响核心业务，需立即排查原因并恢复", "高"),
        ("宽带故障批量处理", "某片区大面积宽带断网，OLT 设备 PON 口故障需紧急处理", "高"),
        ("基站退服抢修", "某 4G 基站因市电断电退服，需派发电车现场保障", "高"),
        ("政企客户季度巡检", "为 VIP 政企客户进行季度网络设备巡检和健康检查", "中"),
        ("天翼云故障排查", "客户云主机 IO 延迟升高，排查存储后端性能问题", "中"),
        ("用户投诉信号差处理", "某小区用户集中投诉 4G 信号差，安排测试优化", "中"),
        ("专线降噪优化", "某数据专线误码率偏高，需逐段测试排查光缆质量", "中"),
        ("视频会议联调保障", "某政企客户重要视频会议网络保障和现场值守", "中"),
        ("SD-WAN 网络优化", "某连锁企业 SD-WAN 网络延迟抖动大，需要 QoS 策略优化", "低"),
    ],
    "custom": [
        ("季度网络应急演练", "组织通信应急演练，模拟光缆中断场景下的业务倒换", "中"),
        ("防汛通信保障部署", "汛期来临前完成重点区域通信设施检查和防汛物资准备", "高"),
        ("安全生产月活动", "组织通信线路施工安全规范和登高作业安全培训", "中"),
        ("员工技能比武", "光缆熔纤技能比武大赛，考察装维人员实操水平", "低"),
        ("季度经营分析会", "通报本季度宽带发展、收入完成、服务指标情况", "高"),
        ("新入职员工培训", "本月新入职 5 位装维工程师的岗前安全培训", "中"),
        ("厂家技术交流", "华为厂家新技术交流会，了解最新光接入产品", "低"),
        ("年底资产盘点", "对辖区内通信线路、设备、备品备件进行年终盘点", "中"),
    ],
}


def _days_ago(n):
    return timezone.now() - timedelta(days=n)


class Command(BaseCommand):
    help = "为全部已有用户的每个页面元素补充逼真的电信业务演示数据（全量替换）"

    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True).exclude(username="星辰AI助手")
        total = users.count()
        self.stdout.write(f"为目标用户填充电信业务数据（共 {total} 人）\n")

        # ── 清除旧的非电信业务数据 ──
        # 删除旧 generic 数据（保留已有部分，只清理旧内容）
        old_titles = [
            "完成周报数据汇总", "整理客户需求文档", "跟进项目进度", "参加跨部门协调会",
            "修复系统告警问题", "更新工作台账", "编写测试用例", "处理用户工单",
            "准备汇报材料", "完成培训课程", "提交报销申请", "设备领用登记",
            "参与技术评审", "完成数据备份", "更新通讯录", "安全检查整改",
            "编写操作手册", "组织团队活动", "处理邮件积压", "核查系统日志",
            "对接新客户", "方案内部评审", "合同归档整理", "环境部署准备",
            "知识库更新", "完成安全培训", "参与应急演练", "优化工作流程",
            "会议纪要整理", "提交调研报告",
        ]
        deleted, _ = Task.objects.filter(title__in=old_titles).delete()
        self.stdout.write(f"  [清理] 旧任务: {deleted} 条")

        old_mat_prefixes = ["工作心得", "常用工具清单", "学习笔记", "工作规划", "会议记录"]
        from django.db.models import Q
        q = Q()
        for p in old_mat_prefixes:
            q |= Q(title__startswith=p)
        deleted_mat, _ = SavedReport.objects.filter(q).delete()
        self.stdout.write(f"  [清理] 旧材料: {deleted_mat} 条")

        # ── 1. Tasks (每个用户 4 条) ──
        task_before = Task.objects.count()
        batch = []
        for user in users:
            existing_task_count = Task.objects.filter(assignee=user).count()
            need = max(0, 4 - existing_task_count)
            if need == 0:
                continue
            picked = random.sample(TASK_TITLES, min(need + 1, len(TASK_TITLES)))
            for title, desc, status in picked[:need]:
                batch.append(Task(
                    title=title[:256],
                    description=desc,
                    status=status,
                    created_by_id=random.choice(list(users.values_list("id", flat=True))),
                    assignee=user,
                    created_at=_days_ago(random.randint(0, 30)),
                    updated_at=_days_ago(random.randint(0, 7)),
                ))
        if batch:
            Task.objects.bulk_create(batch, ignore_conflicts=True)
        self.stdout.write(f"  [✓] 任务: {Task.objects.count()}（新增 {Task.objects.count() - task_before}）")

        # ── 2. Materials (每个用户 4 条) ──
        mat_before = SavedReport.objects.count()
        batch = []
        for user in users:
            existing = SavedReport.objects.filter(user=user).count()
            need = max(0, 4 - existing)
            if need == 0:
                continue
            picked = random.sample(MAT_CONTENT, min(need, len(MAT_CONTENT)))
            for rtype, prefix, content in picked:
                day = _days_ago(random.randint(0, 30))
                batch.append(SavedReport(
                    user=user,
                    title=f"{prefix} {day.strftime('%m-%d')}",
                    report_type=rtype,
                    content=content,
                    source=random.choice(["report_generator", "user_save"]),
                    created_at=day,
                    updated_at=day,
                    is_pinned=random.random() < 0.1,
                ))
        if batch:
            SavedReport.objects.bulk_create(batch, ignore_conflicts=True)
        self.stdout.write(f"  [✓] 材料: {SavedReport.objects.count()}（新增 {SavedReport.objects.count() - mat_before}）")

        # ── 3. Calendar Memos (每个用户 4 条) ──
        memo_before = CalendarMemo.objects.count()
        # Clear old generic memos
        old_memo_titles = ["提交周报", "部门例会", "项目站会", "提交月报", "系统巡检",
                          "培训学习", "报销提交", "安全检查", "工作会议", "方案评审",
                          "客户回访", "数据核对", "知识分享", "计划制定", "问题回顾"]
        CalendarMemo.objects.filter(title__in=old_memo_titles).delete()
        batch = []
        for user in users:
            existing = CalendarMemo.objects.filter(user=user).count()
            need = max(0, 4 - existing)
            if need == 0:
                continue
            picked = random.sample(MEMO_TITLES, min(need, len(MEMO_TITLES)))
            for title, content in picked:
                batch.append(CalendarMemo(
                    user=user,
                    date=timezone.now().date() + timedelta(days=random.randint(-7, 14)),
                    title=title,
                    content=content,
                ))
        if batch:
            CalendarMemo.objects.bulk_create(batch, ignore_conflicts=True)
        self.stdout.write(f"  [✓] 备忘: {CalendarMemo.objects.count()}（新增 {CalendarMemo.objects.count() - memo_before}）")

        # ── 4. Notifications (每个用户 3 条) ──
        # Clear old generic notifications
        old_notif_titles = ["新任务待办", "系统维护通知", "群聊总结已生成", "版本更新通知", "任务催办提醒"]
        Notification.objects.filter(title__in=old_notif_titles).delete()
        notif_before = Notification.objects.count()
        batch = []
        for user in users:
            existing = Notification.objects.filter(user=user).count()
            need = max(0, 3 - existing)
            if need == 0:
                continue
            picked = random.sample(NOTIF_MESSAGES, min(need, len(NOTIF_MESSAGES)))
            for ntype, title, msg in picked:
                batch.append(Notification(
                    user=user,
                    notif_type=ntype,
                    title=title,
                    message=msg,
                    is_read=random.random() < 0.4,
                    created_at=_days_ago(random.randint(0, 14)),
                ))
        if batch:
            Notification.objects.bulk_create(batch, ignore_conflicts=True)
        self.stdout.write(f"  [✓] 通知: {Notification.objects.count()}（新增 {Notification.objects.count() - notif_before}）")

        # ── 5. Events (32 条电信事件, 每个用户至少 3 条) ──
        event_before = Event.objects.count()

        # Build org-based user groups for participant assignment
        city_orgs = ["南京", "苏州", "无锡", "常州", "南通", "徐州", "扬州", "盐城",
                     "镇江", "泰州", "淮安", "连云港", "宿迁"]
        tech_orgs = ["ICNOC", "IBOC", "无线网优中心"]

        city_users = {city: [] for city in city_orgs}
        tech_users = []
        subsidiary_users = {"中电鸿信": [], "号百公司": [], "智恒公司": [],
                           "算力公司": [], "公信公司": [], "全渠": []}
        other_users = []

        for u in users:
            org_name = u.organization.name if u.organization else ""
            if org_name in city_orgs:
                city_users[org_name].append(u)
            elif org_name in tech_orgs:
                tech_users.append(u)
            elif org_name in subsidiary_users:
                subsidiary_users[org_name].append(u)
            else:
                other_users.append(u)

        all_city_users = sum(city_users.values(), [])
        all_subsidiary = sum(subsidiary_users.values(), [])
        all_tech = tech_users + all_city_users + all_subsidiary + other_users

        # Create events (skip if already exist by title)
        created_events = []
        for cat, seeds in EVENT_SEEDS.items():
            for title_template, desc, pri in seeds:
                if Event.objects.filter(title=title_template).exists():
                    continue
                ev_date = _days_ago(random.randint(0, 60))
                priority_map = {"高": "high", "中": "medium", "低": "low"}
                event = Event.objects.create(
                    title=title_template,
                    description=desc,
                    category=cat,
                    priority=priority_map[pri],
                    status=random.choice(["open", "in_progress", "closed"]),
                    start_date=(ev_date - timedelta(days=random.randint(0, 5))).date(),
                    end_date=(ev_date + timedelta(days=random.randint(1, 14))).date(),
                    contact_person=random.choice(list(users.values_list("display_name", flat=True))) or "张工",
                    contact_phone=f"1{random.randint(30, 99)}{random.randint(10000000, 99999999)}",
                    created_by=random.choice(list(users)),
                    created_at=ev_date,
                    updated_at=ev_date + timedelta(hours=random.randint(1, 72)),
                )
                created_events.append(event)

        # Assign participants: each event gets relevant users + fallback to ensure coverage
        assigned_users = set()
        for event in created_events:
            title = event.title
            participants = set()

            # Intelligent org-based assignment
            if any(kw in title for kw in ["5G", "基站", "无线", "网优"]):
                participants.update(tech_users)
                participants.update(random.sample(all_city_users, min(5, len(all_city_users))))
            elif any(kw in title for kw in ["云", "数据中"]):
                participants.update(subsidiary_users["中电鸿信"])
                participants.update(subsidiary_users["智恒公司"])
                participants.update(subsidiary_users["算力公司"])
                participants.update(random.sample(all_city_users, min(3, len(all_city_users))))
            elif any(kw in title for kw in ["光纤入户", "宽带", "装维"]):
                participants.update(all_city_users)
            elif any(kw in title for kw in ["政企", "专线", "银行", "电路", "OTN"]):
                participants.update(tech_users)
                participants.update(all_city_users)
            elif any(kw in title for kw in ["视频", "TV", "天翼高清", "IPTV"]):
                participants.update(subsidiary_users["号百公司"])
                participants.update(random.sample(all_city_users, min(5, len(all_city_users))))
            elif any(kw in title for kw in ["安全", "演练", "防汛", "培训", "技能"]):
                participants.update(random.sample(all_tech, min(20, len(all_tech))))
            elif any(kw in title for kw in ["IDC", "机房", "电源"]):
                participants.update(tech_users)
                participants.update(subsidiary_users["算力公司"])
            elif any(kw in title for kw in ["监控", "雪亮", "门禁", "一卡通"]):
                participants.update(subsidiary_users["公信公司"])
                participants.update(all_city_users)
            elif any(kw in title for kw in ["经营", "资产", "比武", "分析会"]):
                participants.update(random.sample(all_tech, min(20, len(all_tech))))
            elif any(kw in title for kw in ["厂家", "技术交流"]):
                participants.update(random.sample(all_tech, min(10, len(all_tech))))
            elif any(kw in title for kw in ["智慧园区", "智慧校园", "智慧社区"]):
                participants.update(all_city_users)
                participants.update(subsidiary_users["中电鸿信"])
            elif any(kw in title for kw in ["医院", "医疗"]):
                participants.update(all_city_users)
            elif any(kw in title for kw in ["超市", "连锁", "SD-WAN"]):
                participants.update(subsidiary_users["全渠"])
                participants.update(random.sample(all_city_users, min(4, len(all_city_users))))
            elif any(kw in title for kw in ["工业互联"]):
                participants.update(tech_users)
                participants.update(random.sample(all_city_users, min(4, len(all_city_users))))
            elif any(kw in title for kw in ["企业上云"]):
                participants.update(all_subsidiary)
                participants.update(random.sample(all_city_users, min(4, len(all_city_users))))
            else:
                participants.update(random.sample(all_tech, min(10, len(all_tech))))

            # Always add creator
            participants.add(event.created_by)

            # Add a few from 无部门/other if present
            if other_users:
                participants.update(random.sample(other_users, min(3, len(other_users))))

            if participants:
                event.participants.add(*participants)
                assigned_users.update(participants)

        # ── Ensure ALL users have at least 3 events ──
        users_with_few_events = [u for u in users if Event.objects.filter(participants=u).count() < 3]
        if users_with_few_events and created_events:
            self.stdout.write(f"  [补充] 为 {len(users_with_few_events)} 个事件不足的用户补充参与关系...")
            for u in users_with_few_events:
                have_ids = set(Event.objects.filter(participants=u).values_list("id", flat=True))
                # Pick events this user doesn't have yet
                candidates = [e for e in created_events if e.id not in have_ids]
                if not candidates:
                    candidates = list(Event.objects.exclude(participants=u)[:10])
                need = min(3 - len(have_ids), len(candidates))
                if need > 0:
                    for e in random.sample(candidates, need):
                        e.participants.add(u)

        self.stdout.write(f"  [✓] 事件: {Event.objects.count()}（新增 {Event.objects.count() - event_before}）")

        # ── Verify coverage ──
        zero_event_users = [u for u in users if Event.objects.filter(participants=u).count() == 0]
        if zero_event_users:
            self.stdout.write(f"  [!] 仍有 {len(zero_event_users)} 用户无事件: {[u.display_name or u.username for u in zero_event_users]}")

        # ── Summary ──
        self.stdout.write("\n✅ 数据补充完成！")
        self.stdout.write(f"   覆盖用户: {total}")
        self.stdout.write(f"   任务: {Task.objects.count()}")
        self.stdout.write(f"   材料: {SavedReport.objects.count()}")
        self.stdout.write(f"   备忘: {CalendarMemo.objects.count()}")
        self.stdout.write(f"   通知: {Notification.objects.count()}")
        self.stdout.write(f"   事件: {Event.objects.count()}")

        # ── 抽样验证 ──
        self.stdout.write("\n抽样数据（随机 5 个用户）:")
        # Verify event distribution across orgs
        from collections import Counter
        org_event_counts = Counter()
        for u in users:
            ec = Event.objects.filter(participants=u).count()
            org_name = u.organization.name if u.organization else "无部门"
            org_event_counts[org_name] += ec
        self.stdout.write("  各机构事件总数:")
        for org, cnt in sorted(org_event_counts.items(), key=lambda x: -x[1])[:10]:
            self.stdout.write(f"     {org}: {cnt}")

        samples = random.sample(list(users), min(5, total))
        for u in samples:
            t = Task.objects.filter(assignee=u).exclude(status__in=["completed", "cancelled"]).count()
            m = SavedReport.objects.filter(user=u).count()
            c = CalendarMemo.objects.filter(user=u).count()
            n = Notification.objects.filter(user=u).count()
            e = Event.objects.filter(participants=u).count()
            org_name = u.organization.name if u.organization else "无部门"
            self.stdout.write(f"   {u.display_name or u.username} [{org_name}]: 待办={t} 材料={m} 备忘={c} 通知={n} 事件={e}")
