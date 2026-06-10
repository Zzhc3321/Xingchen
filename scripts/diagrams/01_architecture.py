#!/usr/bin/env python3
"""
系统架构图 - 星辰协同平台
Uses Pillow for rendering (supports variable fonts natively)
"""
from PIL import Image, ImageDraw, ImageFont
import os

# ── 颜色方案 ──
C = {
    'bg':       (248, 250, 252),
    'title':    (30, 41, 59),
    'subtitle': (100, 116, 139),

    'user_bg':    (224, 242, 254),
    'user_border':(2, 132, 199),
    'user_text':  (12, 74, 110),

    'gateway_bg':    (240, 249, 255),
    'gateway_border':(56, 189, 248),
    'gateway_text':  (12, 74, 110),

    'app_bg':       (219, 234, 254),
    'app_border':   (37, 99, 235),
    'app_text':     (30, 64, 175),

    'ai_bg':        (243, 232, 255),
    'ai_border':    (147, 51, 234),
    'ai_text':      (76, 29, 149),

    'data_bg':      (254, 243, 199),
    'data_border':  (217, 119, 6),
    'data_text':    (120, 53, 15),

    'infra_bg':     (241, 245, 249),
    'infra_border': (100, 116, 139),
    'infra_text':   (51, 65, 85),

    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'arrow': (148, 163, 184),
}

def get_font(size, bold=False):
    """Load font at given size"""
    path = '/tmp/NotoSansSC.ttf'
    return ImageFont.truetype(path, size)

def draw_round_box(draw, x, y, w, h, fill, border, r=8, width=2):
    """Draw rounded rectangle"""
    draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, outline=border, width=width)

def draw_arrow_down(draw, cx, top, bottom):
    """Draw downward arrow centered at cx from top to bottom"""
    mid = (top + bottom) / 2
    draw.line([(cx, top), (cx, mid)], fill=C['arrow'], width=2)
    # Arrow head
    draw.polygon([(cx-5, mid), (cx+5, mid), (cx, mid+6)], fill=C['arrow'])

def center_text(draw, x, y, text, font, fill, anchor='mm'):
    """Draw centered text"""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x - tw/2
    ty = y - th/2
    draw.text((tx, ty), text, font=font, fill=fill)

def main():
    W, H = 1800, 1200
    img = Image.new('RGB', (W, H), C['bg'])
    draw = ImageDraw.Draw(img)

    f_title = get_font(28)
    f_layer = get_font(16)
    f_comp_name = get_font(14)
    f_comp_desc = get_font(11)
    f_small = get_font(10)

    LAYER_H = 145
    LAYER_GAP = 18
    LEFT = 80
    RIGHT = W - 40
    LAYER_W = RIGHT - LEFT

    # ── Title ──
    center_text(draw, W/2, 38, '星辰协同平台 — 系统架构图', f_title, C['title'])

    layers = [
        ('用户接入层', C['user_bg'], C['user_border'], C['user_text'], [
            ('Web浏览器', 'AdminLTE 3 + Bootstrap 5'),
            ('WebSocket客户端', '实时消息/通知推送'),
            ('移动端适配', '响应式布局适配'),
        ]),
        ('网关与接入层', C['gateway_bg'], C['gateway_border'], C['gateway_text'], [
            ('Daphne ASGI服务器', 'HTTP + WebSocket双协议'),
            ('Django Channels', '协议路由与WS鉴权'),
            ('静态文件服务', '前端资源分发'),
        ]),
        ('业务应用层 (Django)', C['app_bg'], C['app_border'], C['app_text'], [
            ('用户认证模块', '登录/注册/权限'),
            ('事件管理中心', '全生命周期/标签'),
            ('即时通讯模块', '群聊/私聊/回撤'),
            ('好友系统', '请求/搜索/在线状态'),
            ('任务调度系统', '分配/进度/附件'),
            ('通知系统', 'WS实时推送'),
            ('个人中心', '资料/头像/密码'),
            ('仪表盘', '统计/快捷入口'),
        ]),
        ('AI智能服务层', C['ai_bg'], C['ai_border'], C['ai_text'], [
            ('星辰AI助手', 'Dify Workflow API'),
            ('智能上下文', '聊天历史+文件分析'),
            ('@AI触发响应', '群聊AI即时回复'),
        ]),
        ('数据存储层', C['data_bg'], C['data_border'], C['data_text'], [
            ('MySQL数据库', '业务数据持久化'),
            ('Redis缓存', 'Channels消息代理'),
            ('文件存储系统', '头像/附件/图片'),
        ]),
        ('基础设施层', C['infra_bg'], C['infra_border'], C['infra_text'], [
            ('Linux服务器', 'CentOS / Ubuntu'),
            ('Nginx反向代理', '负载均衡/SSL'),
            ('Docker容器化', '部署/扩缩容'),
        ]),
    ]

    start_y = 75

    for i, (layer_name, bg, border, text_color, items) in enumerate(layers):
        y = start_y + i * (LAYER_H + LAYER_GAP)

        # Layer background
        draw_round_box(draw, LEFT, y, LAYER_W, LAYER_H, bg, border, r=10, width=2)

        # Layer label (vertical text on left side)
        lx = LEFT + 10
        ly = y + LAYER_H / 2
        # Draw vertical label
        bbox = draw.textbbox((0, 0), layer_name, font=f_layer)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        # Use each character on its own
        draw.text((lx, ly - th * len(layer_name) / 2), '\n'.join(layer_name), font=f_layer, fill=text_color, align='center')

        # Items
        n = len(items)
        item_area_x = LEFT + 55
        item_area_w = LAYER_W - 65
        item_w = item_area_w / n - 10
        item_h = LAYER_H * 0.65
        item_y = y + (LAYER_H - item_h) / 2

        for j, (name, desc) in enumerate(items):
            ix = item_area_x + j * (item_w + 10)
            draw_round_box(draw, ix, item_y, item_w, item_h, C['white'], border, r=6, width=1)

            cx = ix + item_w / 2
            center_text(draw, cx, item_y + item_h * 0.4, name, f_comp_name, text_color)
            center_text(draw, cx, item_y + item_h * 0.75, desc, f_comp_desc, text_color)

        # Arrow to next layer
        if i < len(layers) - 1:
            arrow_y = y + LAYER_H
            next_y = start_y + (i + 1) * (LAYER_H + LAYER_GAP)
            cx = W / 2
            draw_arrow_down(draw, cx, arrow_y, next_y)

    # ── Bottom info ──
    center_text(draw, W/2, H - 20,
                '技术栈：Django 6.0 + Daphne 4.1 + Channels 4.1 + Redis + MySQL + AdminLTE 3 + Bootstrap 5',
                f_small, C['subtitle'])

    # ── Protocol labels on right side ──
    flow_info = [
        ('HTTP REST API', 240),
        ('WebSocket 实时通信', 400),
        ('Dify AI Workflow API', 555),
        ('ORM 数据访问', 700),
        ('系统运维', 855),
    ]
    for label, fy in flow_info:
        center_text(draw, W - 30, fy, label, f_small, C['subtitle'])

    output_dir = os.path.join(os.path.dirname(__file__), '../../media/diagrams')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, '01_系统架构图.png')
    img.save(output_path, quality=95, dpi=(200, 200))
    print(f"✅ 系统架构图已生成: {output_path}")
    print(f"   尺寸: {img.size}, 大小: {os.path.getsize(output_path) / 1024:.1f} KB")

if __name__ == '__main__':
    main()
