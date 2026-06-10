"""Import all users from the organization table.

Creates organizations and users, then establishes default friendships.

Usage:
    python manage.py import_users          # Create orgs + users + friendships
    python manage.py import_users --friendships-only   # Only create friendships
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from myapp.members.models import Organization, User, Friendship

# Full user data: (序号, 单位, 姓名, 手机号码)
USER_DATA = [
    (1, "南京", "姚浩然", "15335170236"),
    (2, "南京", "石怡杰", "15335170362"),
    (3, "南京", "李睿智", "15335170386"),
    (4, "南京", "张继溥", "15335170380"),
    (5, "南京", "娄登科", "15715675056"),
    (6, "南京", "戈世奇", "13776626127"),
    (7, "苏州", "周润志", "19951012727"),
    (8, "苏州", "顾斯佳", "17751121112"),
    (9, "苏州", "赵华众", "18915560441"),
    (10, "苏州", "时艺轩", "13295116383"),
    (11, "苏州", "张苏南", "19825232080"),
    (12, "无锡", "宁洛函", "15306180937"),
    (13, "无锡", "汤家辉", "18915200995"),
    (14, "无锡", "蒋浩", "15298666885"),
    (15, "无锡", "李智涛", "19901448128"),
    (16, "无锡", "曾辉", "15070709982"),
    (17, "常州", "刘昊", "18001502263"),
    (18, "常州", "张成娟", "18001502086"),
    (19, "常州", "杨海涛", "17315115225"),
    (20, "常州", "王默涵", "18001501387"),
    (21, "常州", "万啸栋", "18118389228"),
    (22, "常州", "朱书艺", "18001503990"),
    (23, "常州", "严培艺", "18915010011"),
    (24, "常州", "吴嘉玥", "18001506956"),
    (25, "常州", "陈梦一", "15895965076"),
    (26, "南通", "李玉达", "18962780859"),
    (27, "南通", "吴博文", "18962933611"),
    (28, "南通", "许宏伟", "15312618633"),
    (29, "南通", "纪慧文", "18015916210"),
    (30, "南通", "刘阳", "18012288889"),
    (31, "南通", "茅黄锦", "18082002075"),
    (32, "南通", "丁海蕾", "18962933919"),
    (33, "徐州", "程言欣", "18020567366"),
    (34, "徐州", "陈国顺", "13372237881"),
    (35, "徐州", "刘骐瑜", "18796382668"),
    (36, "徐州", "袁畅", "17300514123"),
    (37, "徐州", "袁赛", "18114832519"),
    (38, "扬州", "陆成", "19305273739"),
    (39, "扬州", "邓依霖", "19900818722"),
    (40, "扬州", "李天玮", "19352727951"),
    (41, "扬州", "戴逸鹏", "18252565182"),
    (42, "扬州", "黄立", "15952709182"),
    (43, "扬州", "王志强", "15651902275"),
    (44, "扬州", "王俊", "15949571440"),
    (45, "盐城", "唐修文", "17305150172"),
    (46, "盐城", "单国强", "18912500166"),
    (47, "盐城", "戴湘为", "18914685223"),
    (48, "盐城", "王子翔", "17300671271"),
    (49, "盐城", "俞为绩", "15851141175"),
    (50, "镇江", "虞则", "17768766039"),
    (51, "镇江", "张镇东", "18021219532"),
    (52, "泰州", "刘雨琪", "18061010693"),
    (53, "泰州", "陈凯阳", "17314773339"),
    (54, "泰州", "徐悦", "17766028019"),
    (55, "泰州", "叶亚雯", "18061015063"),
    (56, "淮安", "朱芸琳", "18952391391"),
    (57, "淮安", "代杰", "17766132561"),
    (58, "连云港", "杨蕊菡", "18136575360"),
    (59, "连云港", "颜廷坚", "15850789952"),
    (60, "宿迁", "张岩", "19352760312"),
    (61, "宿迁", "姜前", "17327569277"),
    (62, "ICNOC", "郭瀞元", "15301582576"),
    (63, "ICNOC", "程海东", "15301582571"),
    (64, "ICNOC", "李广通", "15996291908"),
    (65, "IBOC", "孙开胜", "15301582516"),
    (66, "IBOC", "刘毅", "15301582521"),
    (67, "IBOC", "王喻星", "15301582519"),
    (68, "全渠", "朱久旭", "15301582925"),
    (69, "全渠", "肖晴晗", "18207226156"),
    (70, "无线网优中心", "汤雪岩", "15301582542"),
    (71, "中电鸿信", "申国强", "18051998869"),
    (72, "中电鸿信", "徐声健", "18051998870"),
    (73, "中电鸿信", "闫焕文", "18013835868"),
    (74, "中电鸿信", "程瑶", "18051998851"),
    (75, "中电鸿信", "徐运奇", "18900660625"),
    (76, "中电鸿信", "王鑫", "18900660870"),
    (77, "中电鸿信", "徐霖涛", "18900660353"),
    (78, "中电鸿信", "汤晓宇", "18900660852"),
    (79, "中电鸿信", "魏云鹏", "18900660903"),
    (80, "中电鸿信", "吴昕璐", "15162126030"),
    (81, "中电鸿信", "薛棋源", "15751016119"),
    (82, "中电鸿信", "苏雨瑶", "15165200458"),
    (83, "中电鸿信", "万洁珉", "18915401843"),
    (84, "号百公司", "黄耕", "15366188326"),
    (85, "号百公司", "钱铖", "15366188330"),
    (86, "号百公司", "朱敏婕", "15366188347"),
    (87, "号百公司", "张盛翔", "15366188349"),
    (88, "号百公司", "孙劭涵", "15366188346"),
    (89, "号百公司", "蒋子涵", "15366188355"),
    (90, "号百公司", "邹佳成", "15366188357"),
    (91, "号百公司", "尤馨影", "15366188358"),
    (92, "公信公司", "史振奇", "18051998808"),
    (93, "公信公司", "陈钰", "18900660572"),
    (94, "智恒公司", "钱坤", "18066110072"),
    (95, "智恒公司", "黄勇", "18051998968"),
    (96, "智恒公司", "郑子吟", "18051998990"),
    (97, "智恒公司", "张洁颖", "19802568964"),
    (98, "智恒公司", "强朝蓬", "18752054082"),
    (99, "算力公司", "徐振轩", "15301582539"),
    (100, "算力公司", "何鹏飞", "15301582538"),
]

DEFAULT_PASSWORD = "123456"


def _get_orgs():
    """Get or create all organizations."""
    seen = set()
    orgs = {}
    for _, org_name, _, _ in USER_DATA:
        if org_name not in seen:
            seen.add(org_name)
            org, _ = Organization.objects.get_or_create(name=org_name)
            orgs[org_name] = org
    return orgs


def _create_users(orgs, stdout):
    """Create all users."""
    created = 0
    skipped = 0
    for seq, org_name, name, phone in USER_DATA:
        user, is_new = User.objects.get_or_create(
            username=phone,
            defaults={
                'display_name': name,
                'phone': phone,
                'organization': orgs[org_name],
            },
        )
        if is_new:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            created += 1
        else:
            skipped += 1
    stdout.write(f"  Users: {created} created, {skipped} already exist")
    return created


def _create_friendships(stdout):
    """Make all users default friends with each other."""
    all_users = list(User.objects.exclude(username='ai_robot'))
    total = len(all_users)
    existing = 0
    created = 0
    for i in range(total):
        for j in range(i + 1, total):
            u1, u2 = all_users[i], all_users[j]
            f1, f1_new = Friendship.objects.get_or_create(user=u1, friend=u2)
            f2, f2_new = Friendship.objects.get_or_create(user=u2, friend=u1)
            created += f1_new + f2_new
            existing += (not f1_new) + (not f2_new)
    stdout.write(f"  Friendships: {created} created, {existing} already exist")


class Command(BaseCommand):
    help = 'Import organization users and create default friendships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--friendships-only',
            action='store_true',
            help='Only create friendships (skip org/user creation)',
        )

    def handle(self, *args, **options):
        if options.get('friendships_only'):
            self.stdout.write("Creating friendships only...")
            _create_friendships(self.stdout)
            self.stdout.write(self.style.SUCCESS("Done."))
            return

        self.stdout.write("Creating organizations...")
        orgs = _get_orgs()
        self.stdout.write(f"  {len(orgs)} organizations ready")

        self.stdout.write("Creating users...")
        with transaction.atomic():
            _create_users(orgs, self.stdout)

        self.stdout.write("Creating default friendships...")
        _create_friendships(self.stdout)

        self.stdout.write(self.style.SUCCESS(
            "Import complete. All users can login with password 123456"
        ))
