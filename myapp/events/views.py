import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from myapp.chat.models import Conversation
from myapp.members.models import User, Tag
from .models import Event, EventGroup, CalendarMemo


def _json(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return {}


@login_required
def events_view(request):
    qs = Event.objects.filter(participants=request.user).select_related('created_by').prefetch_related('tags').order_by('-updated_at')
    category = request.GET.get('category', '')
    if category:
        qs = qs.filter(category=category)
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
    tag_id = request.GET.get('tag', '')
    if tag_id:
        qs = qs.filter(tags__id=tag_id)
    priority = request.GET.get('priority', '')
    if priority:
        qs = qs.filter(priority=priority)
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.exclude(status='archived')
    elif status_filter == 'archived':
        qs = qs.filter(status='archived')

    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 15))
    page = max(1, page)
    page_size = min(50, max(1, page_size))

    total = qs.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages) if total > 0 else 1

    start = (page - 1) * page_size
    end = start + page_size
    items = qs[start:end]

    data = []
    for e in items:
        group = getattr(e, 'group', None)
        data.append({
            'id': e.id, 'title': e.title, 'description': e.description,
            'category': e.category, 'priority': e.priority, 'status': e.status,
            'start_date': e.start_date.isoformat() if e.start_date else None,
            'end_date': e.end_date.isoformat() if e.end_date else None,
            'contact_person': e.contact_person or '',
            'contact_phone': e.contact_phone or '',
            'amount': str(e.amount) if e.amount is not None else None,
            'archived_at': e.archived_at.isoformat() if e.archived_at else None,
            'created_by': e.created_by.username, 'created_by_id': e.created_by.id,
            'created_at': e.created_at.isoformat(),
            'updated_at': e.updated_at.isoformat(),
            'group_id': group.conversation_id if group else None,
            'group_archived': group.archived if group else False,
            'tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in e.tags.all()],
        })
    # Also return counts per category (single query instead of N)
    from django.db.models import Count
    cat_counts = Event.objects.filter(participants=request.user).values('category').annotate(count=Count('id'))
    counts = {cat: 0 for cat, _ in Event.CATEGORY_CHOICES}
    for row in cat_counts:
        counts[row['category']] = row['count']
    return JsonResponse({
        'events': data,
        'counts': counts,
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
def create_event_view(request):
    data = _json(request)
    title = (data.get('title') or '').strip()
    if not title:
        return JsonResponse({'detail': '事件标题不能为空'}, status=400)
    start_date_str = data.get('start_date') or ''
    end_date_str = data.get('end_date') or ''
    amount_str = data.get('amount') or ''
    from django.utils.dateparse import parse_date
    event = Event.objects.create(
        title=title,
        description=(data.get('description') or '').strip(),
        category=data.get('category', 'custom'),
        priority=data.get('priority', 'medium'),
        start_date=parse_date(start_date_str) if start_date_str else None,
        end_date=parse_date(end_date_str) if end_date_str else None,
        contact_person=(data.get('contact_person') or '').strip(),
        contact_phone=(data.get('contact_phone') or '').strip(),
        amount=float(amount_str) if amount_str else None,
        created_by=request.user,
    )
    participant_ids = data.get('participant_ids', [])
    if participant_ids:
        event.participants.add(*User.objects.filter(id__in=participant_ids))
    event.participants.add(request.user)
    return JsonResponse({'id': event.id})


@login_required
def event_detail_view(request, event_id):
    e = get_object_or_404(Event, id=event_id)
    if request.user not in e.participants.all() and request.user != e.created_by:
        return JsonResponse({'detail': 'forbidden'}, status=403)
    return JsonResponse({
        'id': e.id, 'title': e.title, 'description': e.description,
        'category': e.category, 'priority': e.priority, 'status': e.status,
        'start_date': e.start_date.isoformat() if e.start_date else None,
        'end_date': e.end_date.isoformat() if e.end_date else None,
        'contact_person': e.contact_person or '',
        'contact_phone': e.contact_phone or '',
        'amount': str(e.amount) if e.amount is not None else None,
    })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def create_event_group_view(request, event_id):
    data = _json(request)
    e = get_object_or_404(Event, id=event_id)
    if request.user != e.created_by and request.user not in e.participants.all():
        return JsonResponse({'detail': 'forbidden'}, status=403)
    if hasattr(e, 'group'):
        return JsonResponse({'group_id': e.group.conversation_id})
    title = (data.get('title') or e.title).strip()
    conv = Conversation.objects.create(conversation_type='group', title=title, created_by=request.user)
    # Combine event participants with custom selected members
    extra_ids = data.get('participant_ids', [])
    extra_users = User.objects.filter(id__in=extra_ids) if extra_ids else []
    members = set(list(e.participants.all()) + list(extra_users))
    members.add(request.user)
    # Add AI robot by default
    from myapp.ai_robot import get_robot_user
    robot = get_robot_user()
    if robot:
        members.add(robot)
    conv.participants.add(*members)
    for u in members:
        from myapp.chat.models import ConversationMember
        ConversationMember.objects.get_or_create(conversation=conv, user=u, defaults={'role': 'admin' if u == request.user else 'member'})
    EventGroup.objects.create(event=e, conversation=conv)
    # Notify all members about the new group
    from myapp.notify import notify_group_created, notify_group_invite
    creator_name = request.user.display_name or request.user.username
    for u in members:
        if u.id == request.user.id:
            continue
        notify_group_created(u.id, conv.id, title, creator_name, e.title)
        # Also mark as group invite for non-participants who were added
        if u not in e.participants.all():
            notify_group_invite(u.id, conv.id, title, creator_name)
    return JsonResponse({'group_id': conv.id})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def archive_event_view(request, event_id):
    e = get_object_or_404(Event, id=event_id)
    if request.user != e.created_by and request.user not in e.participants.all():
        return JsonResponse({'detail': 'forbidden'}, status=403)
    from django.utils import timezone
    e.status = 'archived'
    e.archived_at = timezone.now()
    e.save(update_fields=['status', 'archived_at', 'updated_at'])
    if hasattr(e, 'group'):
        e.group.archived = True
        e.group.save(update_fields=['archived'])
    return JsonResponse({'detail': 'ok'})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def restore_event_view(request, event_id):
    """Restore an archived event. Only the creator can restore."""
    e = get_object_or_404(Event, id=event_id)
    if request.user != e.created_by:
        return JsonResponse({'detail': '只有事件创建者可以恢复'}, status=403)
    e.status = 'open'
    e.archived_at = None
    e.save(update_fields=['status', 'archived_at', 'updated_at'])
    if hasattr(e, 'group'):
        e.group.archived = False
        e.group.save(update_fields=['archived'])
    return JsonResponse({'detail': 'ok'})


# ===== Tag Management =====

@login_required
def tag_list_view(request):
    """List all available tags."""
    tags = Tag.objects.all().order_by('name')
    return JsonResponse({
        'tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in tags]
    })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def event_tags_view(request, event_id):
    """Add/remove tags for an event."""
    e = get_object_or_404(Event, id=event_id)
    if request.user != e.created_by and request.user not in e.participants.all():
        return JsonResponse({'detail': 'forbidden'}, status=403)
    data = _json(request)
    action = data.get('action', 'set')
    tag_ids = data.get('tag_ids', [])
    if action == 'add':
        for tid in tag_ids:
            tag = get_object_or_404(Tag, id=tid)
            e.tags.add(tag)
    elif action == 'remove':
        for tid in tag_ids:
            e.tags.remove(tid)
    else:
        e.tags.set(Tag.objects.filter(id__in=tag_ids))
    return JsonResponse({'detail': 'ok', 'tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in e.tags.all()]})


# ===== Calendar Memo =====

@login_required
def memo_list_view(request):
    """Get memos for a specific date or month."""
    date_str = request.GET.get('date', '')
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    qs = CalendarMemo.objects.filter(user=request.user)
    if date_str:
        qs = qs.filter(date=date_str)
    elif year and month:
        try:
            qs = qs.filter(date__year=int(year), date__month=int(month))
        except (ValueError, TypeError):
            return JsonResponse({'detail': '无效的年份或月份'}, status=400)
    qs = qs.order_by('-created_at')[:50]
    return JsonResponse({
        'memos': [{'id': m.id, 'date': m.date.isoformat(), 'title': m.title,
                    'content': m.content, 'created_at': m.created_at.isoformat()}
                  for m in qs]
    })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def memo_create_view(request):
    """Create a calendar memo."""
    data = _json(request)
    date_str = data.get('date', '')
    title = (data.get('title') or '').strip()
    if not date_str or not title:
        return JsonResponse({'detail': '日期和标题不能为空'}, status=400)
    from django.utils.dateparse import parse_date
    d = parse_date(date_str)
    if not d:
        return JsonResponse({'detail': '日期格式无效'}, status=400)
    memo = CalendarMemo.objects.create(
        user=request.user, date=d, title=title,
        content=(data.get('content') or '').strip(),
    )
    return JsonResponse({'id': memo.id, 'detail': 'ok'})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def memo_delete_view(request, memo_id):
    """Delete a calendar memo."""
    memo = get_object_or_404(CalendarMemo, id=memo_id, user=request.user)
    memo.delete()
    return JsonResponse({'detail': 'ok'})


@login_required
def memo_dates_view(request):
    """Get dates that have memos/tasks in a month (for calendar dots)."""
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    if not year or not month:
        return JsonResponse({'detail': 'year and month required'}, status=400)
    try:
        y, m = int(year), int(month)
    except (ValueError, TypeError):
        return JsonResponse({'detail': '无效的年份或月份'}, status=400)
    qs = CalendarMemo.objects.filter(user=request.user, date__year=y, date__month=m)
    memo_dates = set(qs.values_list('date', flat=True))
    # Also get dates with tasks
    from myapp.members.models import Task
    task_dates = set(Task.objects.filter(
        assignee=request.user,
        created_at__year=y,
        created_at__month=m,
    ).values_list('created_at', flat=True))
    task_dates = {d.date() for d in task_dates}
    return JsonResponse({
        'memo_dates': [d.isoformat() for d in memo_dates],
        'task_dates': [d.isoformat() for d in task_dates],
    })


@csrf_exempt
@require_http_methods(['POST'])
def external_create_event_view(request):
    """External API: create an event using X-API-Key authentication.
    Allows external systems (scripts, integrations) to create events."""
    from django.conf import settings

    api_key = request.META.get('HTTP_X_API_KEY', '')
    expected_key = getattr(settings, 'EXTERNAL_API_KEY', '')
    if not api_key or api_key != expected_key:
        return JsonResponse({'detail': '无效的 API Key'}, status=401)

    data = _json(request)
    title = (data.get('title') or '').strip()
    if not title:
        return JsonResponse({'detail': '事件标题不能为空'}, status=400)

    from django.utils.dateparse import parse_date

    # Create event without requiring a specific user — use first active user or a designated robot
    from myapp.members.models import User
    creator = User.objects.filter(is_active=True).order_by('id').first()
    if not creator:
        return JsonResponse({'detail': '系统中没有可用用户'}, status=500)

    amount_str = data.get('amount') or ''
    event = Event.objects.create(
        title=title,
        description=(data.get('description') or '').strip(),
        category=data.get('category', 'custom'),
        priority=data.get('priority', 'medium'),
        start_date=parse_date(data.get('start_date', '')) if data.get('start_date') else None,
        end_date=parse_date(data.get('end_date', '')) if data.get('end_date') else None,
        contact_person=(data.get('contact_person') or '').strip(),
        contact_phone=(data.get('contact_phone') or '').strip(),
        amount=float(amount_str) if amount_str else None,
        created_by=creator,
    )
    event.participants.add(creator)

    # If external_source is provided, save it somewhere accessible
    external_source = data.get('external_source', '')
    if external_source:
        from myapp.members.models import Tag
        tag, _ = Tag.objects.get_or_create(name=f'来源:{external_source}')
        event.tags.add(tag)

    return JsonResponse({
        'id': event.id,
        'title': event.title,
        'external_source': external_source,
        'detail': '事件创建成功',
    })
