import json
from io import BytesIO

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Announcement, SavedReport


def _render(request, template, nav=None):
    return render(request, template, {'active_nav': nav})


@login_required
def dashboard_view(request):
    return _render(request, 'dashboard.html', 'dashboard')


@login_required
def dashboard_data_view(request):
    return _render(request, 'dashboard_data.html', 'dashboard_data')


@login_required
def chat_page(request):
    return _render(request, 'chat.html', 'chat')


@login_required
def friends_page(request):
    return _render(request, 'friends.html', 'friends')


@login_required
def profile_page(request):
    return _render(request, 'profile.html', 'profile')


@login_required
def events_page(request):
    return _render(request, 'events.html', 'events')


def login_page(request):
    return render(request, 'login.html')


def register_page(request):
    return render(request, 'register.html')


def api_announcements(request):
    """API: 获取通知公告列表"""
    qs = Announcement.objects.filter(is_active=True)
    return JsonResponse({
        'announcements': [{
            'id': a.id,
            'title': a.title,
            'content': a.content,
            'is_pinned': a.is_pinned,
            'created_at': a.created_at.isoformat(),
        } for a in qs],
    })


@login_required
def materials_page(request):
    """我的材料页面"""
    return render(request, 'materials.html', {'active_nav': 'materials'})


@login_required
def api_materials_list(request):
    """API: 获取用户的材料列表（分页 + 置顶 + 统计）"""
    report_type = request.GET.get('type', '')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 15))
    search_q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'newest')  # newest or oldest

    page = max(1, page)
    page_size = min(50, max(1, page_size))

    qs = SavedReport.objects.filter(user=request.user)
    if report_type:
        types = report_type.split(',')
        qs = qs.filter(report_type__in=types)
    if search_q:
        qs = qs.filter(title__icontains=search_q)

    # Count by type for stats
    stats = {}
    for t_key, t_label in SavedReport.REPORT_TYPES:
        stats[t_key] = SavedReport.objects.filter(user=request.user, report_type=t_key).count()

    # Order: pinned first, then by date
    if sort == 'newest':
        qs = qs.order_by('-is_pinned', '-created_at')
    else:
        qs = qs.order_by('-is_pinned', 'created_at')

    total = qs.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages) if total > 0 else 1

    start = (page - 1) * page_size
    end = start + page_size
    items = qs[start:end]

    return JsonResponse({
        'materials': [{
            'id': r.id,
            'title': r.title,
            'report_type': r.report_type,
            'content': r.content[:500],  # preview length
            'source': r.source,
            'is_pinned': r.is_pinned,
            'related_conv_id': r.related_conv_id,
            'created_at': r.created_at.isoformat(),
            'updated_at': r.updated_at.isoformat() if r.updated_at else r.created_at.isoformat(),
        } for r in items],
        'stats': stats,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
        },
    })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_materials_save(request):
    """API: 保存一份材料到我的材料"""
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': '无效的 JSON'}, status=400)

    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    report_type = data.get('report_type', 'user_doc')
    source = data.get('source', 'user_save')
    related_conv_id = data.get('related_conv_id')

    if not title or not content:
        return JsonResponse({'detail': '标题和内容不能为空'}, status=400)

    report = SavedReport.objects.create(
        user=request.user,
        title=title,
        report_type=report_type,
        content=content,
        source=source,
        related_conv_id=related_conv_id,
    )
    return JsonResponse({
        'id': report.id,
        'title': report.title,
        'created_at': report.created_at.isoformat(),
    })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_materials_delete(request, material_id):
    """API: 删除一份材料"""
    material = get_object_or_404(SavedReport, id=material_id, user=request.user)
    material.delete()
    return JsonResponse({'detail': 'ok'})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_materials_batch_delete(request):
    """API: 批量删除材料"""
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': '无效的 JSON'}, status=400)
    ids = data.get('ids', [])
    if not ids:
        return JsonResponse({'detail': '请选择要删除的材料'}, status=400)
    deleted, _ = SavedReport.objects.filter(id__in=ids, user=request.user).delete()
    return JsonResponse({'detail': f'已删除 {deleted} 项'})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_materials_toggle_pin(request, material_id):
    """API: 切换材料的置顶状态"""
    material = get_object_or_404(SavedReport, id=material_id, user=request.user)
    material.is_pinned = not material.is_pinned
    material.save(update_fields=['is_pinned'])
    return JsonResponse({'id': material.id, 'is_pinned': material.is_pinned})


@login_required
def api_materials_export(request, material_id):
    """API: 导出材料（支持 markdown / txt）"""
    fmt = request.GET.get('format', 'markdown')
    material = get_object_or_404(SavedReport, id=material_id, user=request.user)

    from django.utils import timezone
    created_str = timezone.localtime(material.created_at).strftime('%Y-%m-%d %H:%M')

    if fmt == 'txt':
        content = f"标题：{material.title}\n"
        content += f"创建时间：{created_str}\n"
        content += f"来源：{material.get_source_display()}\n"
        content += "=" * 40 + "\n\n"
        content += material.content
        content_type = 'text/plain; charset=utf-8'
        ext = 'txt'
    else:
        content = f"# {material.title}\n\n"
        content += f"> 创建时间：{created_str}　来源：{material.get_source_display()}\n\n"
        content += "---\n\n"
        content += material.content
        content_type = 'text/markdown; charset=utf-8'
        ext = 'md'

    safe_title = material.title.replace('/', '_').replace('\\', '_') or 'material'
    filename = f"{safe_title}.{ext}"
    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_materials_rename(request, material_id):
    """API: 重命名材料标题"""
    material = get_object_or_404(SavedReport, id=material_id, user=request.user)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': '无效的 JSON'}, status=400)
    title = (data.get('title') or '').strip()
    if not title:
        return JsonResponse({'detail': '标题不能为空'}, status=400)
    material.title = title
    material.save(update_fields=['title'])
    return JsonResponse({'id': material.id, 'title': material.title})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def api_materials_edit(request, material_id):
    """API: 编辑材料标题和内容"""
    material = get_object_or_404(SavedReport, id=material_id, user=request.user)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': '无效的 JSON'}, status=400)
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    if not title or not content:
        return JsonResponse({'detail': '标题和内容不能为空'}, status=400)
    material.title = title
    material.content = content
    material.save(update_fields=['title', 'content'])
    return JsonResponse({'id': material.id, 'title': material.title})


def _md_to_reportlab(md_text, body_style):
    """Convert Markdown text to a list of reportlab flowable elements.
    Handles headings, lists, code blocks, tables, blockquotes, HR, and inline formatting.
    """
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    import mistune
    import re

    # Mistune HTML renderer for inline formatting
    md_html = mistune.create_markdown(renderer='html')

    elements = []
    lines = md_text.split('\n')
    i = 0
    n = len(lines)

    # Helper: convert inline markdown to reportlab-safe HTML
    def _inline(text):
        """Convert markdown inline formatting to basic HTML that reportlab can render."""
        if not text:
            return ''
        # Use mistune to render a fragment, then strip outer <p> if any
        html = md_html(text).strip()
        if html.startswith('<p>') and html.endswith('</p>'):
            html = html[3:-4]
        return html

    def _add_para(html_text, style=None, space_after=6):
        if html_text.strip():
            elements.append(Paragraph(html_text, style or body_style))
            elements.append(Spacer(1, space_after * 0.3 * mm))

    code_style = ParagraphStyle(
        'CodeBlock', parent=body_style,
        fontSize=9, leading=13, leftIndent=8,
        backColor=colors.HexColor('#f4f4f4'),
        textColor=colors.HexColor('#333333'),
    )
    heading_styles = {}
    for level in range(1, 7):
        sizes = {1: 16, 2: 14, 3: 13, 4: 12, 5: 11, 6: 11}
        heading_styles[level] = ParagraphStyle(
            f'Heading{level}', parent=body_style,
            fontSize=sizes[level], leading=sizes[level] + 6,
            spaceBefore=10, spaceAfter=4,
            textColor=colors.HexColor('#1a1a2e'),
        )
    blockquote_style = ParagraphStyle(
        'BlockQuote', parent=body_style,
        leftIndent=12, fontSize=10.5, leading=17,
        textColor=colors.HexColor('#555555'),
        backColor=colors.HexColor('#f9f9f9'),
    )
    list_body_style = ParagraphStyle(
        'ListItem', parent=body_style,
        fontSize=10.5, leading=17, spaceAfter=2,
    )

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Blank line
        if not stripped:
            i += 1
            continue

        # Code block (```)
        if stripped.startswith('```'):
            info = stripped[3:].strip()  # language hint
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            # Skip closing ```
            if i < n:
                i += 1
            code_text = '\n'.join(code_lines)
            if code_text:
                safe = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                elements.append(Paragraph(
                    f'<font size="8"><b>{info}</b></font>' if info else '',
                    code_style
                ))
                elements.append(Paragraph(safe, code_style))
                elements.append(Spacer(1, 4 * 0.3 * mm))
            continue

        # Thematic break (--- or *** or ___)
        if re.match(r'^-{3,}$', stripped) or re.match(r'^\*{3,}$', stripped) or re.match(r'^_{3,}$', stripped):
            elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
            elements.append(Spacer(1, 4))
            i += 1
            continue

        # Blockquote
        if stripped.startswith('> '):
            quote_lines = []
            while i < n and lines[i].strip().startswith('> '):
                quote_lines.append(lines[i].strip()[2:])
                i += 1
            quote_text = ' '.join(quote_lines)
            elements.append(Paragraph(
                f'<i>{_inline(quote_text)}</i>',
                blockquote_style
            ))
            elements.append(Spacer(1, 4))
            continue

        # Unordered list (gather all consecutive list items)
        if re.match(r'^[\-\*]\s', stripped):
            items = []
            while i < n:
                s = lines[i].strip()
                m = re.match(r'^[\-\*]\s+(.*)', s)
                if not m:
                    break
                items.append(m.group(1))
                i += 1
            for item in items:
                bullet = '•'
                nested = item.startswith('  ')
                indent = 12 if nested else 6
                elements.append(Paragraph(
                    f'<font size="10">{bullet}</font>&nbsp;&nbsp;{_inline(item.strip())}',
                    ParagraphStyle('BulletItem', parent=list_body_style, leftIndent=indent)
                ))
            elements.append(Spacer(1, 4))
            continue

        # Ordered list
        if re.match(r'^\d+\.\s', stripped):
            items = []
            start_num = None
            while i < n:
                s = lines[i].strip()
                m = re.match(r'^(\d+)\.\s+(.*)', s)
                if not m:
                    break
                num = int(m.group(1))
                if start_num is None:
                    start_num = num
                items.append((num, m.group(2)))
                i += 1
            for num, item in items:
                elements.append(Paragraph(
                    f'<b>{num}.</b>&nbsp;&nbsp;{_inline(item.strip())}',
                    ParagraphStyle('NumberItem', parent=list_body_style, leftIndent=6)
                ))
            elements.append(Spacer(1, 4))
            continue

        # Table (| col | col |)
        if stripped.startswith('|') and stripped.endswith('|'):
            rows = []
            align_row = None
            while i < n:
                s = lines[i].strip()
                if not s.startswith('|'):
                    break
                # Check if this is an alignment row (|---|)
                if re.match(r'^\|[-:\s|]+\|$', s) and all(c in '-:| ' for c in s):
                    align_row = len(rows)
                    i += 1
                    continue
                # Parse table row
                cells = [c.strip() for c in s.split('|')[1:-1]]
                rows.append(cells)
                i += 1
            if rows:
                # First row is header if there's an alignment row or multiple rows
                header = rows[0] if len(rows) > 1 else None
                data = rows[1:] if len(rows) > 1 else rows
                if align_row is not None and len(rows) > 1:
                    data = rows[1:] if align_row == 0 else rows
                    # align_row might actually be the separator, skip it
                    pass

                col_count = max(len(r) for r in rows)
                # Build table data
                tbl_data = []
                if header:
                    tbl_data.append(header)
                tbl_data.extend(data)

                tbl = Table(tbl_data, hAlign='LEFT')
                tbl_style_cmds = [
                    ('FONTNAME', (0, 0), (-1, -1), 'NotoSansSC'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('LEADING', (0, 0), (-1, -1), 14),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]
                if header:
                    tbl_style_cmds += [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f4ff')),
                        ('FONTNAME', (0, 0), (-1, 0), 'NotoSansSC'),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                    ]
                tbl.setStyle(TableStyle(tbl_style_cmds))
                elements.append(tbl)
                elements.append(Spacer(1, 6))
            continue

        # Heading
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            style = heading_styles.get(level, body_style)
            elements.append(Paragraph(f'<b>{_inline(text)}</b>', style))
            elements.append(Spacer(1, 4))
            i += 1
            continue

        # Regular paragraph — collect consecutive lines
        para_lines = []
        while i < n:
            s = lines[i].strip()
            if not s:
                break
            # Stop at block-level markers
            if s.startswith('```') or s.startswith('> ') or re.match(r'^[\-\*]\s', s) or \
               re.match(r'^\d+\.\s', s) or s.startswith('|') or \
               re.match(r'^#{1,6}\s', s) or re.match(r'^-{3,}$', s):
                break
            para_lines.append(s)
            i += 1

        if para_lines:
            para_text = ' '.join(para_lines)
            # Convert line breaks within paragraph
            para_html = _inline(para_text)
            elements.append(Paragraph(para_html, body_style))
            elements.append(Spacer(1, 4))

    return elements


@login_required
def api_materials_pdf(request, material_id):
    """API: 下载材料为 PDF 文件"""
    material = get_object_or_404(SavedReport, id=material_id, user=request.user)

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os
    import re
    from django.conf import settings

    # Register CJK font for Chinese character support
    font_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'fonts', 'NotoSansSC-Regular.ttf')
    pdfmetrics.registerFont(TTFont('NotoSansSC', font_path))

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20*mm, bottomMargin=20*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )

    title_style = ParagraphStyle(
        'CustomTitle',
        fontName='NotoSansSC',
        fontSize=18, leading=24, spaceAfter=12,
        textColor=colors.HexColor('#1a73e8'),
    )
    meta_style = ParagraphStyle(
        'Meta',
        fontName='NotoSansSC',
        fontSize=9, leading=13, spaceAfter=20,
        textColor=colors.HexColor('#64748b'),
    )
    body_style = ParagraphStyle(
        'Body',
        fontName='NotoSansSC',
        fontSize=11, leading=18, spaceAfter=8,
    )

    from django.utils import timezone
    created_str = timezone.localtime(material.created_at).strftime('%Y-%m-%d %H:%M')

    elements = []
    elements.append(Paragraph(material.title, title_style))
    elements.append(Paragraph(f"创建时间：{created_str}　来源：{material.get_source_display()}", meta_style))
    elements.append(Spacer(1, 6*mm))

    # Convert markdown content to reportlab elements
    elements += _md_to_reportlab(material.content, body_style)

    doc.build(elements)
    pdf_bytes = buf.getvalue()
    buf.close()

    # Build safe filename
    safe_title = material.title.replace('/', '_').replace('\\', '_') or 'material'
    filename = f"{safe_title}.pdf"

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = len(pdf_bytes)
    return response
