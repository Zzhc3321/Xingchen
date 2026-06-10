#!/usr/bin/env python3
"""
功能模块图 - 星辰协同平台
Shows all functional modules in a hierarchical tree structure
"""
from PIL import Image, ImageDraw, ImageFont
import os, math

C = {
    'bg':       (248, 250, 252),
    'title':    (30, 41, 59),

    # Module colors
    'auth':     (59, 130, 246),    # blue
    'event':    (239, 68, 68),     # red
    'chat':     (16, 185, 129),    # green
    'friend':   (245, 158, 11),    # amber
    'task':     (139, 92, 246),    # violet
    'ai':       (168, 85, 247),    # purple
    'notif':    (236, 72, 153),    # pink
    'profile':  (14, 165, 233),    # sky
    'dash':     (99, 102, 241),    # indigo
}

MODULE_COLORS = [
    (59, 130, 246), (239, 68, 68), (16, 185, 129),
    (245, 158, 11), (139, 92, 246), (168, 85, 247),
    (236, 72, 153), (14, 165, 233), (99, 102, 241),
]

def get_font(size):
    return ImageFont.truetype('/tmp/NotoSansSC.ttf', size)

def draw_round_box(draw, x, y, w, h, fill, border=None, r=8, width=1):
    """Draw rounded rectangle"""
    if border:
        draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, outline=border, width=width)
    else:
        draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, width=0)

def center_text(draw, x, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw/2, y - th/2), text, font=font, fill=fill)

def draw_tree_node(draw, x, y, name, sub_items, color, font_title, font_item):
    """Draw a module group with its sub-items"""
    box_w = 200
    box_h = 30 + len(sub_items) * 28
    r = 10

    # Header bar
    draw_round_box(draw, x, y, box_w, 34, color, r=r)
    center_text(draw, x + box_w/2, y + 17, name, font_title, (255, 255, 255))

    # Sub-items below
    for i, item in enumerate(sub_items):
        iy = y + 38 + i * 28
        # Light background
        lighter = tuple(min(c + 60, 255) for c in color)
        draw_round_box(draw, x + 8, iy, box_w - 16, 24, lighter, color, r=5, width=1)
        center_text(draw, x + box_w/2, iy + 12, item, font_item, (30, 41, 59))

    return box_w, 38 + len(sub_items) * 28

def main():
    W, H = 2400, 1400
    img = Image.new('RGB', (W, H), C['bg'])
    draw = ImageDraw.Draw(img)

    f_main = get_font(30)
    f_module = get_font(16)
    f_sub = get_font(13)
    f_legend = get_font(11)

    # ── Title ──
    center_text(draw, W/2, 40, '星辰协同平台 — 功能模块图', f_main, C['title'])

    # ── Module definitions ──
    modules = [
        ('用户认证', MODULE_COLORS[0], [
            '用户名/手机号登录', '注册（含头像上传）',
            '记住密码（30天）', '权限管理',
        ]),
        ('事件管理', MODULE_COLORS[1], [
            '全生命周期管理', '售前/售中/售后/定制',
            '优先级标签', '联系人/金额信息',
            '标签管理', '归档/恢复',
        ]),
        ('即时通讯', MODULE_COLORS[2], [
            '群聊/私聊', 'WebSocket实时消息',
            'Markdown渲染', '文件/图片上传',
            '2分钟内消息撤回', '已读状态',
            '会话归档/搜索', '@AI助手触发',
        ]),
        ('好友系统', MODULE_COLORS[3], [
            '好友搜索添加', '好友请求审批',
            '在线状态显示', '好友管理',
        ]),
        ('任务调度', MODULE_COLORS[4], [
            '任务创建分配', '进度追踪',
            '附件上传', '实时通知',
            '待办/进行/完成/取消',
        ]),
        ('AI助手', MODULE_COLORS[5], [
            '@星辰AI助手', 'Dify Workflow API',
            '聊天历史上下文', '文件分析',
            '智能回复', '异步处理',
        ]),
        ('通知系统', MODULE_COLORS[6], [
            'WebSocket实时推送', 'HTTP轮询(60s)',
            '好友/消息/任务通知', '通知已读管理',
            '自动重连机制',
        ]),
        ('个人中心', MODULE_COLORS[7], [
            '资料编辑', '头像裁剪上传',
            '在线/勿扰/离线状态', '密码修改',
            '通知开关', '日历备忘录',
        ]),
        ('仪表盘', MODULE_COLORS[8], [
            '数据统计卡片', '事件分类饼图',
            '我的任务', '日历（备忘点）',
            '在线好友', '最近动态',
            '快捷入口', '公告栏',
        ]),
    ]

    # ── Layout: 3 columns x 3 rows ──
    COLS = 3
    ROWS = 3
    BOX_W = 240
    BOX_H = 300
    START_X = 180
    START_Y = 100
    GAP_X = 60
    GAP_Y = 40

    for idx, (name, color, items) in enumerate(modules):
        col = idx % COLS
        row = idx // COLS
        x = START_X + col * (BOX_W + GAP_X)
        y = START_Y + row * (BOX_H + GAP_Y)

        # Draw module group with all sub-items
        # Header
        draw_round_box(draw, x, y, BOX_W, 38, color, r=10)
        center_text(draw, x + BOX_W/2, y + 19, name, f_module, (255, 255, 255))

        # Sub-items
        for i, item in enumerate(items):
            iy = y + 44 + i * 30
            # Alternating light background
            bg_shade = tuple(min(c + 60 + (10 if i % 2 == 0 else 0), 255) for c in color)
            draw_round_box(draw, x + 10, iy, BOX_W - 20, 26, bg_shade, color, r=5, width=1)
            center_text(draw, x + BOX_W/2, iy + 13, item, f_sub, (30, 41, 59))

        # Connection lines between layers
        if col < COLS - 1:
            cx1 = x + BOX_W
            cx2 = START_X + (col + 1) * (BOX_W + GAP_X)
            cy = y + BOX_H / 2
            draw.line([(cx1 + 5, cy), (cx2 - 5, cy)], fill=(200, 200, 200), width=1)
            # Arrow
            draw.polygon([(cx2 - 8, cy - 4), (cx2 - 8, cy + 4), (cx2 - 2, cy)], fill=(200, 200, 200))

    # ── Legend ──
    legend_y = START_Y + ROWS * (BOX_H + GAP_Y) + 20
    center_text(draw, W/2, legend_y, '平台覆盖：用户认证 | 事件管理 | 即时通讯 | 好友系统 | 任务调度 | AI助手 | 通知系统 | 个人中心 | 数据仪表盘',
                f_legend, (100, 116, 139))

    output_dir = os.path.join(os.path.dirname(__file__), '../../media/diagrams')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, '02_功能模块图.png')
    img.save(output_path, quality=95, dpi=(200, 200))
    print(f"✅ 功能模块图已生成: {output_path}")
    print(f"   尺寸: {img.size}, 大小: {os.path.getsize(output_path) / 1024:.1f} KB")

if __name__ == '__main__':
    main()
