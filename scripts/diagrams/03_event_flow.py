#!/usr/bin/env python3
"""
事件生命周期业务流程图 - 星辰协同平台
"""
from PIL import Image, ImageDraw, ImageFont
import os

C = {
    'bg':       (248, 250, 252),
    'title':    (30, 41, 59),
    'text':     (30, 41, 59),
    'subtitle': (100, 116, 139),
    'white':    (255, 255, 255),
    'arrow':    (148, 163, 184),

    # Stage colors
    'create':   (59, 130, 246),     # blue
    'pre':      (245, 158, 11),     # amber
    'in_progress': (16, 185, 129),  # green
    'after':    (99, 102, 241),     # indigo
    'archive':  (100, 116, 139),    # gray
}

def get_font(size):
    return ImageFont.truetype('/tmp/NotoSansSC.ttf', size)

def draw_round_box(draw, x, y, w, h, fill, border=None, r=10, width=2):
    if border:
        draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, outline=border, width=int(width))
    else:
        draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, width=0)

def center_text(draw, x, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw/2, y - th/2), text, font=font, fill=fill)

def draw_step(draw, x, y, w, h, title, desc_lines, color, f_title, f_desc):
    """Draw a process step box"""
    # Header
    draw_round_box(draw, x, y, w, 40, color, r=8)
    center_text(draw, x + w/2, y + 20, title, f_title, C['white'])

    # Content area
    draw_round_box(draw, x, y + 40, w, h - 40, C['white'], color, r=0, width=1.5)
    # Bottom rounded corners
    draw_round_box(draw, x, y + h - 15, w, 15, C['white'], color, r=0, width=0)
    draw_round_box(draw, x, y + h - 15, w, 16, C['white'], color, r=8, width=1.5)

    for i, line in enumerate(desc_lines):
        center_text(draw, x + w/2, y + 58 + i * 24, line, f_desc, C['text'])

def draw_arrow_right(draw, x1, y, x2):
    """Draw right-pointing arrow"""
    draw.line([(x1, y), (x2 - 12, y)], fill=C['arrow'], width=2)
    draw.polygon([(x2 - 12, y - 6), (x2 - 12, y + 6), (x2, y)], fill=C['arrow'])

def draw_arrow_down_short(draw, x, y1, y2):
    """Draw downward arrow"""
    draw.line([(x, y1), (x, y2 - 8)], fill=C['arrow'], width=2)
    draw.polygon([(x - 6, y2 - 8), (x + 6, y2 - 8), (x, y2)], fill=C['arrow'])

def draw_decision(draw, cx, cy, text, font, fill):
    """Draw a diamond decision node"""
    r = 22
    points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    draw.polygon(points, fill=C['white'], outline=C['arrow'], width=2)
    center_text(draw, cx, cy, text, font, fill)

def main():
    W, H = 2000, 1100
    img = Image.new('RGB', (W, H), C['bg'])
    draw = ImageDraw.Draw(img)

    f_title = get_font(26)
    f_step_title = get_font(16)
    f_desc = get_font(12)
    f_small = get_font(11)
    f_label = get_font(13)

    # ── Title ──
    center_text(draw, W/2, 35, '星辰协同平台 — 事件生命周期业务流程图', f_title, C['title'])

    # ── Swimlane rows ──
    # Row 1: Create → Assign → Categorize
    # Row 2: Pre-sales → In-sales → After-sales
    # Row 3: Review → Archive

    # Layout
    step_w = 210
    step_h = 170
    arrow_gap = 30
    start_x = 80
    row1_y = 80
    row2_y = 340
    row3_y = 600

    # ═══ ROW 1: Event Creation ═══
    # Step 1: Create Event
    draw_step(draw, start_x, row1_y, step_w, step_h, '① 创建事件',
        ['填写事件标题', '选择分类与优先级', '填写联系人信息', '设置起止日期', '添加参与人员'],
        C['create'], f_step_title, f_desc)

    # Arrow
    draw_arrow_right(draw, start_x + step_w, row1_y + step_h/2, start_x + step_w + arrow_gap + step_w)

    # Step 2: Auto-create group
    sx2 = start_x + step_w + arrow_gap + step_w
    draw_step(draw, sx2, row1_y, step_w, step_h, '② 创建群聊',
        ['自动创建事件群聊', '邀请所有参与者', '自动添加AI助手', '群成员即时通知'],
        C['create'], f_step_title, f_desc)

    draw_arrow_right(draw, sx2 + step_w, row1_y + step_h/2, sx2 + step_w + arrow_gap + step_w)

    # Step 3: Dispatch tasks
    sx3 = sx2 + step_w + arrow_gap + step_w
    draw_step(draw, sx3, row1_y, step_w, step_h, '③ 任务分派',
        ['创建关联任务', '指定负责人', '设定截止日期', '上传相关附件', '任务状态追踪'],
        C['create'], f_step_title, f_desc)

    draw_arrow_right(draw, sx3 + step_w, row1_y + step_h/2, sx3 + step_w + arrow_gap + step_w)

    # Step 4: Real-time collaboration
    sx4 = sx3 + step_w + arrow_gap + step_w
    draw_step(draw, sx4, row1_y, step_w, step_h, '④ 协同处理',
        ['群聊即时沟通', '@AI助手智能回复', '文件/图片共享', '消息撤回/已读'],
        C['pre'], f_step_title, f_desc)

    # Down arrow from row1 to row2
    draw_arrow_down_short(draw, sx4 + step_w/2, row1_y + step_h, row2_y)

    # ═══ ROW 2: Event Lifecycle ═══
    # Swimlane label
    center_text(draw, 45, row2_y + 80, '事\n件\n阶\n段', f_desc, C['subtitle'])
    draw.line([(55, row2_y), (55, row2_y + 200)], fill=C['subtitle'], width=1)

    stage_w = 195
    stage_h = 160
    stage_gap = 50
    stage_y = row2_y + 20
    stage_start_x = 80

    stages = [
        ('售前阶段', C['pre'], [
            '需求沟通与确认',
            '初步方案制定',
            '报价与预算',
            '项目评估',
        ]),
        ('售中阶段', C['in_progress'], [
            '合同签署与执行',
            '资源调配',
            '进度跟踪管理',
            '质量把控',
        ]),
        ('售后阶段', C['after'], [
            '交付验收',
            '客户反馈收集',
            '问题跟踪处理',
            '满意度评估',
        ]),
    ]

    for i, (sname, color, items) in enumerate(stages):
        sx = stage_start_x + i * (stage_w + stage_gap)
        # Header
        draw_round_box(draw, sx, stage_y, stage_w, 36, color, r=8)
        center_text(draw, sx + stage_w/2, stage_y + 18, sname, f_step_title, C['white'])
        # Content
        content_y = stage_y + 40
        draw_round_box(draw, sx, content_y, stage_w, stage_h - 40, C['white'], color, r=0, width=1.5)
        draw_round_box(draw, sx, stage_y + stage_h - 15, stage_w, 16, C['white'], color, r=8, width=1.5)
        for j, item in enumerate(items):
            center_text(draw, sx + stage_w/2, content_y + 15 + j * 28, f'• {item}', f_desc, C['text'])

        # Arrows between stages
        if i < len(stages) - 1:
            draw_arrow_right(draw, sx + stage_w, stage_y + stage_h/2, sx + stage_w + stage_gap)

    # Down arrow from row2 (post-sale) to row3
    last_stage_x = stage_start_x + 2 * (stage_w + stage_gap)
    draw_arrow_down_short(draw, last_stage_x + stage_w/2, stage_y + stage_h, row3_y)

    # ═══ ROW 3: Archive ═══
    r3y = row3_y + 20

    # Decision: Review
    dec_cx = 300
    draw_decision(draw, dec_cx, r3y + 60, '审核\n通过?', f_label, C['text'])

    # No path (back)
    draw.text((dec_cx + 30, r3y + 30), '否', font=f_label, fill=(239, 68, 68))
    # Arrow back up
    back_y = r3y + 60
    draw.line([(dec_cx + 22, back_y), (dec_cx + 80, back_y), (dec_cx + 80, 80 + step_h + 20), (sx4 + step_w/2, 80 + step_h + 20)], fill=(239, 68, 68), width=2)
    center_text(draw, dec_cx + 120, r3y + 35, '返回修改', f_small, (239, 68, 68))

    # Yes: Archive
    draw_arrow_right(draw, dec_cx + 22, back_y, 520)

    archive_x = 520
    draw_step(draw, archive_x, r3y, 250, 120, '⑤ 事件归档',
        ['归档后只读', '历史记录可追溯', '群聊保留可查阅', '支持重新激活'],
        C['archive'], f_step_title, f_desc)

    draw_arrow_right(draw, archive_x + 250, r3y + 60, 830)

    # End
    end_cx = 850
    draw_round_box(draw, end_cx, r3y + 20, 150, 80, C['create'], r=15)
    center_text(draw, end_cx + 75, r3y + 60, '流程结束', f_step_title, C['white'])

    # ── Legend ──
    legend_y = 900
    draw_round_box(draw, 100, legend_y, W - 200, 100, (241, 245, 249), r=10)

    center_text(draw, 200, legend_y + 20, '图例说明', f_desc, C['subtitle'])

    legends = [
        ('创建阶段', C['create']),
        ('售前阶段', C['pre']),
        ('售中阶段', C['in_progress']),
        ('售后阶段', C['after']),
        ('归档阶段', C['archive']),
    ]
    for i, (lname, color) in enumerate(legends):
        lx = 180 + i * 280
        draw_round_box(draw, lx, legend_y + 38, 100, 20, color, r=5)
        center_text(draw, lx + 50, legend_y + 48, lname, f_small, C['white'])
        center_text(draw, lx + 160, legend_y + 48, f'{["事件创建 → 群聊生成 → 任务分配 → 协同处理 → 分阶段跟进 → 审核归档", ""][0]}', f_small, C['subtitle'])

    # Bottom flow summary
    center_text(draw, W/2, 1030,
        '核心流程：创建事件 → 自动生成群聊 → 分派任务 → 售前/售中/售后协同 → 审核归档',
        f_desc, C['subtitle'])

    output_dir = os.path.join(os.path.dirname(__file__), '../../media/diagrams')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, '03_事件生命周期流程图.png')
    img.save(output_path, quality=95, dpi=(200, 200))
    print(f"✅ 事件生命周期流程图已生成: {output_path}")
    print(f"   尺寸: {img.size}, 大小: {os.path.getsize(output_path) / 1024:.1f} KB")

if __name__ == '__main__':
    main()
