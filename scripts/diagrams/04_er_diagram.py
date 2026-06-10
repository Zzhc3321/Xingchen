#!/usr/bin/env python3
"""
数据关系 ER 图 - 星辰协同平台
Shows core entities and their relationships
"""
from PIL import Image, ImageDraw, ImageFont
import os

C = {
    'bg':       (248, 250, 252),
    'title':    (30, 41, 59),
    'text':     (30, 41, 59),
    'subtitle': (100, 116, 139),
    'white':    (255, 255, 255),
    'line':     (203, 213, 225),
    'arrow':    (148, 163, 184),

    # Entity categories
    'user_c':   (59, 130, 246),     # blue
    'chat_c':   (16, 185, 129),     # green
    'event_c':  (239, 68, 68),      # red
    'task_c':   (139, 92, 246),     # violet
    'notif_c':  (236, 72, 153),     # pink
    'memo_c':   (245, 158, 11),     # amber
}

def get_font(size):
    return ImageFont.truetype('/tmp/NotoSansSC.ttf', size)

def draw_round_box(draw, x, y, w, h, fill, border=None, r=8, width=2):
    if border:
        draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, outline=border, width=int(width))
    else:
        draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, width=0)

def center_text(draw, x, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw/2, y - th/2), text, font=font, fill=fill)

def draw_entity(draw, x, y, w, h, name, fields, color, f_title, f_field, f_pk):
    """Draw a database entity box"""
    # Header
    draw_round_box(draw, x, y, w, 32, color, r=6)
    center_text(draw, x + w/2, y + 16, name, f_title, C['white'])

    # Field list
    fy = y + 36
    for i, field in enumerate(fields):
        is_pk = field.startswith('PK ')
        fg = f_pk if is_pk else f_field
        txt_color = color if is_pk else C['text']
        prefix = '🔑 ' if is_pk else '  '
        # Alternate row background
        if i % 2 == 0:
            draw_round_box(draw, x + 4, fy, w - 8, 22, (248, 250, 252), r=3, width=0)
        draw.text((x + 10, fy + 3), f'{prefix}{field}', font=fg, fill=txt_color)
        fy += 22

def draw_relation_line(draw, x1, y1, x2, y2, label, f_label):
    """Draw a line between two entities with label"""
    draw.line([(x1, y1), (x2, y2)], fill=C['arrow'], width=2)
    # Label at midpoint
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    # Background for label
    bbox = draw.textbbox((0, 0), label, font=f_label)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw_round_box(draw, mx - tw/2 - 4, my - th/2 - 2, tw + 8, th + 4, C['bg'], C['line'], r=4, width=1)
    center_text(draw, mx, my, label, f_label, C['subtitle'])

def draw_crow_foot(draw, x, y, direction, multiplicity):
    """Draw crow's foot notation"""
    size = 8
    points = []
    if direction == 'right':
        points = [(x, y), (x - size, y - size), (x - size, y + size)]
        # Cross line for "many"
        draw.line([(x - size, y - size - 3), (x - size, y + size + 3)], fill=C['arrow'], width=1)
    elif direction == 'left':
        points = [(x, y), (x + size, y - size), (x + size, y + size)]
        draw.line([(x + size, y - size - 3), (x + size, y + size + 3)], fill=C['arrow'], width=1)
    if points:
        draw.polygon(points, fill=C['arrow'])

def main():
    W, H = 2000, 1400
    img = Image.new('RGB', (W, H), C['bg'])
    draw = ImageDraw.Draw(img)

    f_main = get_font(26)
    f_entity = get_font(15)
    f_field = get_font(12)
    f_pk = get_font(12)
    f_rel = get_font(11)
    f_note = get_font(10)

    # ── Title ──
    center_text(draw, W/2, 30, '星辰协同平台 — 核心数据关系图 (ER)', f_main, C['title'])

    # ── Entity definitions ──
    ENT_W = 280
    ENT_H = 260

    entities = [
        # (x, y, w, h, name, fields, color)
        (100, 70, ENT_W, 200, 'User (用户)', [
            'PK id (主键)',
            'username (用户名)',
            'password (密码)',
            'display_name (显示名)',
            'phone (手机号)',
            'avatar (头像URL)',
            'online_status (在线状态)',
            'organization (所属组织)',
        ], C['user_c']),

        (100, 340, ENT_W, 180, 'Organization (组织)', [
            'PK id (主键)',
            'name (组织名称)',
            'description (描述)',
        ], C['user_c']),

        (100, 590, ENT_W, 200, 'Friendship (好友关系)', [
            'PK id (主键)',
            'FK user_id (用户)',
            'FK friend_id (好友)',
            'created_at (建立时间)',
        ], C['user_c']),

        (100, 850, ENT_W, 160, 'FriendRequest (好友请求)', [
            'PK id (主键)',
            'FK from_user (请求方)',
            'FK to_user (接收方)',
            'status (状态)',
            'message (附言)',
        ], C['user_c']),

        # Chat entities - right column
        (550, 70, ENT_W, 220, 'Conversation (会话)', [
            'PK id (主键)',
            'type (类型: 私聊/群聊)',
            'name (会话名称)',
            'is_archived (已归档)',
            'created_at (创建时间)',
        ], C['chat_c']),

        (550, 350, ENT_W, 200, 'ConversationMember (会话成员)', [
            'PK id (主键)',
            'FK conversation (会话)',
            'FK user (用户)',
            'role (角色: 成员/管理员)',
            'joined_at (加入时间)',
        ], C['chat_c']),

        (550, 610, ENT_W, 280, 'Message (消息)', [
            'PK id (主键)',
            'FK conversation (会话)',
            'FK sender (发送者)',
            'content (消息内容)',
            'msg_type (消息类型)',
            'file_url (附件URL)',
            'is_revoked (已撤回)',
            'created_at (发送时间)',
        ], C['chat_c']),

        (550, 950, ENT_W, 180, 'ReadState (已读状态)', [
            'PK id (主键)',
            'FK conversation (会话)',
            'FK user (用户)',
            'last_read_at (最后阅读时间)',
        ], C['chat_c']),

        # Event entities - far right
        (1050, 70, ENT_W, 250, 'Event (事件)', [
            'PK id (主键)',
            'title (事件标题)',
            'category (售前/售中/售后)',
            'priority (优先级)',
            'contact_person (联系人)',
            'amount (金额)',
            'start_date / end_date',
            'is_archived (已归档)',
        ], C['event_c']),

        (1050, 380, ENT_W, 180, 'EventGroup (事件群聊)', [
            'PK id (主键)',
            'FK event (事件)',
            'FK conversation (群聊)',
            'created_at (创建时间)',
        ], C['event_c']),

        (1050, 620, ENT_W, 260, 'Tag (标签)', [
            'PK id (主键)',
            'name (标签名称)',
            'color (颜色)',
        ], C['task_c']),

        # Bottom entities
        (1050, 950, ENT_W, 220, 'Task (任务)', [
            'PK id (主键)',
            'FK creator (创建者)',
            'FK assignee (负责人)',
            'title (任务标题)',
            'status (待办/进行/完成)',
            'file_url (附件)',
        ], C['task_c']),

        (1500, 70, ENT_W, 260, 'Notification (通知)', [
            'PK id (主键)',
            'FK recipient (接收者)',
            'notification_type (类型)',
            'title (标题)',
            'content (内容)',
            'related_link (相关链接)',
            'is_read (已读)',
        ], C['notif_c']),

        (1500, 400, ENT_W, 180, 'CalendarMemo (日历备忘)', [
            'PK id (主键)',
            'FK user (用户)',
            'memo_date (备忘日期)',
            'content (备忘内容)',
            'created_at (创建时间)',
        ], C['memo_c']),

        (1500, 650, ENT_W, 200, 'Announcement (公告)', [
            'PK id (主键)',
            'title (公告标题)',
            'content (公告内容)',
            'is_active (是否启用)',
            'created_at (发布时间)',
        ], C['notif_c']),
    ]

    # Draw all entities
    for x, y, w, h, name, fields, color in entities:
        draw_entity(draw, x, y, w, h, name, fields, color, f_entity, f_field, f_pk)

    # ── Relationship lines ──
    rels = [
        # User -> Organization
        (240, 270, 240, 340, 'N:1 属于', 'right'),
        # User -> Friendship
        (240, 270, 240, 590, '1:N 好友', 'right'),
        # User -> FriendRequest
        (240, 270, 240, 850, '1:N 请求', 'right'),
        # User -> ConversationMember
        (380, 160, 550, 420, 'N:M', 'right'),
        # Conversation -> ConversationMember
        (690, 290, 690, 350, '1:N', 'right'),
        # Conversation -> Message
        (690, 290, 690, 610, '1:N', 'right'),
        # Conversation -> ReadState
        (690, 290, 690, 950, '1:N', 'right'),
        # User -> Message (sender)
        (380, 270, 550, 740, '1:N 发送', 'right'),
        # Event -> EventGroup
        (1190, 320, 1190, 380, '1:N', 'right'),
        # Conversation -> EventGroup
        (830, 160, 1190, 430, '1:1', 'right'),
        # User -> Task (creator)
        (380, 270, 1050, 1020, '1:N 创建', 'right'),
        # User -> Task (assignee)
        (380, 270, 1050, 1080, 'N:1 负责', 'right'),
        # User -> Notification
        (380, 270, 1500, 180, '1:N', 'right'),
        # User -> CalendarMemo
        (380, 270, 1500, 490, '1:N', 'right'),
    ]

    # Simple relationship labels (positioned manually)
    # We draw these as simple text lines between entities
    # User (240, 170) -> Org (240, 430)
    _draw_rel(draw, 320, 270, 320, 340, '属于', '1', 'N', f_rel, 'right')
    _draw_rel(draw, 240, 300, 240, 590, '好友', '1', 'N', f_rel, 'down')
    _draw_rel(draw, 240, 370, 240, 850, '好友请求', '1', 'N', f_rel, 'down')
    _draw_rel(draw, 380, 190, 550, 420, '成员', 'N', 'M', f_rel, 'right')
    _draw_rel(draw, 690, 310, 690, 350, '包含成员', '1', 'N', f_rel, 'down')
    _draw_rel(draw, 690, 320, 690, 610, '包含消息', '1', 'N', f_rel, 'down')
    _draw_rel(draw, 690, 320, 690, 950, '已读记录', '1', 'N', f_rel, 'down')
    _draw_rel(draw, 380, 270, 550, 760, '发送消息', '1', 'N', f_rel, 'right')
    _draw_rel(draw, 1190, 330, 1190, 380, '关联', '1', 'N', f_rel, 'down')
    _draw_rel(draw, 830, 220, 1190, 445, '绑定群聊', '1', '1', f_rel, 'right')
    _draw_rel(draw, 380, 270, 1050, 1080, '创建/负责', '1', 'N', f_rel, 'right')
    _draw_rel(draw, 380, 270, 1500, 190, '接收通知', '1', 'N', f_rel, 'right')
    _draw_rel(draw, 380, 270, 1500, 485, '日历备忘', '1', 'N', f_rel, 'right')
    _draw_rel(draw, 1050, 870, 1050, 950, '有任务', '1', 'N', f_rel, 'down')

    # ── Legend ──
    legend_y = 1220
    draw_round_box(draw, 200, legend_y, W - 400, 60, (241, 245, 249), r=10)

    legend_items = [
        ('用户体系', C['user_c']),
        ('聊天体系', C['chat_c']),
        ('事件体系', C['event_c']),
        ('任务体系', C['task_c']),
        ('通知体系', C['notif_c']),
        ('备忘', C['memo_c']),
    ]
    for i, (lname, color) in enumerate(legend_items):
        lx = 280 + i * 260
        draw_round_box(draw, lx, legend_y + 12, 60, 22, color, r=5)
        center_text(draw, lx + 30, legend_y + 23, lname, f_note, C['white'])
        itext = ['用户/组织/好友', '会话/消息/成员', '事件/群聊/标签', '任务分配追踪', '通知推送管理', '日历备忘录'][i]
        center_text(draw, lx + 130, legend_y + 23, itext, f_note, C['subtitle'])

    # ── Relation notation ──
    center_text(draw, W/2, legend_y + 45,
        '关系标记: 1 (一端)  |  N / M (多端)  |  实体颜色按业务域分组',
        f_note, C['subtitle'])

    output_dir = os.path.join(os.path.dirname(__file__), '../../media/diagrams')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, '04_数据关系ER图.png')
    img.save(output_path, quality=95, dpi=(200, 200))
    print(f"✅ ER 图已生成: {output_path}")
    print(f"   尺寸: {img.size}, 大小: {os.path.getsize(output_path) / 1024:.1f} KB")

def _draw_rel(draw, x1, y1, x2, y2, label, multi1, multi2, font, direction):
    """Draw relationship line between entities with multiplicity labels"""
    draw.line([(x1, y1), (x2, y2)], fill=C['arrow'], width=1)

    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw_round_box(draw, mx - tw/2 - 4, my - th/2 - 2, tw + 8, th + 4, C['bg'], C['line'], r=4, width=1)
    center_text(draw, mx, my, label, font, C['subtitle'])

    # Multiplicity labels at endpoints
    if direction == 'right':
        center_text(draw, x1, y1, multi1, font, C['subtitle'])
        center_text(draw, x2, y2, multi2, font, C['subtitle'])
    elif direction == 'down':
        center_text(draw, x1, y1, multi1, font, C['subtitle'])
        center_text(draw, x1, y2, multi2, font, C['subtitle'])

if __name__ == '__main__':
    main()
