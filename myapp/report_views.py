"""Report generation views — generate reports via Dify API and return stats for charts."""

import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from myapp.ai_robot import call_report_api_sync
from myapp.chat.models import Conversation, Message
from myapp.events.models import Event
from myapp.members.models import Task


def _json(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return {}


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def generate_report_view(request):
    """Generate a report (daily/weekly) via Dify API."""
    data = _json(request)
    report_type = data.get('report_type', 'daily')
    date_from_str = data.get('date_from', '')
    date_to_str = data.get('date_to', '')

    # Default to last 7 days if no range specified
    today = timezone.now().date()
    if not date_to_str:
        date_to_str = today.isoformat()
    if not date_from_str:
        if report_type == 'weekly':
            date_from_str = (today - timedelta(days=7)).isoformat()
        else:
            date_from_str = (today - timedelta(days=1)).isoformat()

    # Gather stats for the date range
    from django.utils.dateparse import parse_date
    d_from = parse_date(date_from_str)
    d_to = parse_date(date_to_str)
    if not d_from or not d_to:
        return JsonResponse({'detail': '日期格式无效，请使用 YYYY-MM-DD'}, status=400)

    # Query events in range
    events_qs = Event.objects.filter(
        created_at__date__gte=d_from,
        created_at__date__lte=d_to,
    )
    total_events = events_qs.count()
    cat_counts = events_qs.values('category').annotate(count=Count('id'))
    cat_detail = {row['category']: row['count'] for row in cat_counts}

    # Query tasks in range
    tasks_qs = Task.objects.filter(
        created_at__date__gte=d_from,
        created_at__date__lte=d_to,
    )
    total_tasks = tasks_qs.count()
    task_statuses = tasks_qs.values('status').annotate(count=Count('id'))
    task_detail = {row['status']: row['count'] for row in task_statuses}

    # Query messages in range
    msg_count = Message.objects.filter(
        created_at__date__gte=d_from,
        created_at__date__lte=d_to,
    ).count()

    # Build context text for Dify
    cat_labels = {'pre_sales': '售前', 'in_sales': '售中', 'after_sales': '售后', 'custom': '自定义'}
    task_labels = {'pending': '待处理', 'in_progress': '进行中', 'completed': '已完成', 'cancelled': '已取消'}

    # Prepend user personal info
    user = request.user
    user_display = user.display_name or user.username

    context_lines = [
        f"统计周期：{date_from_str} 至 {date_to_str}",
        f"报告类型：{'周报' if report_type == 'weekly' else '日报'}",
        f"生成人：{user_display}（{user.username}）",
        "",
        "一、事件统计",
        f"  新建事件总数：{total_events}",
    ]
    for cat_key, cat_name in cat_labels.items():
        context_lines.append(f"  {cat_name}：{cat_detail.get(cat_key, 0)}")

    context_lines.extend([
        "",
        "二、任务统计",
        f"  新建任务总数：{total_tasks}",
    ])
    for st_key, st_name in task_labels.items():
        context_lines.append(f"  {st_name}：{task_detail.get(st_key, 0)}")

    context_lines.extend([
        "",
        f"三、消息数量：{msg_count}",
    ])

    context_text = '\n'.join(context_lines)

    # Call Dify API — pass actual stats data as input_text (not a dry prompt)
    reply = call_report_api_sync(context_text)

    # Save to SavedReport
    from myapp.models import SavedReport
    report = SavedReport.objects.create(
        user=request.user,
        title=f"{'周报' if report_type == 'weekly' else '日报'} {date_from_str} ~ {date_to_str}",
        report_type=report_type,
        content=reply,
        source='report_generator',
    )

    return JsonResponse({
        'report_id': report.id,
        'title': report.title,
        'content': reply,
        'created_at': report.created_at.isoformat(),
    })


@login_required
def stats_view(request):
    """Return statistics for ECharts dashboard."""
    today = timezone.now().date()

    # Event trend: last 7 days
    event_trend = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = Event.objects.filter(created_at__date=d).count()
        event_trend.append({'date': d.isoformat(), 'count': count})

    # Task distribution
    task_statuses = Task.objects.values('status').annotate(count=Count('id'))
    task_distribution = {row['status']: row['count'] for row in task_statuses}

    # Event category distribution
    cat_counts = Event.objects.values('category').annotate(count=Count('id'))
    cat_distribution = {row['category']: row['count'] for row in cat_counts}

    # Message count
    msg_count_7d = Message.objects.filter(
        created_at__date__gte=today - timedelta(days=7),
    ).count()

    return JsonResponse({
        'event_trend': event_trend,
        'task_distribution': task_distribution,
        'cat_distribution': cat_distribution,
        'msg_count_7d': msg_count_7d,
    })
