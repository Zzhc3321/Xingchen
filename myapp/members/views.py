import json
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import User, FriendRequest, Friendship, Notification, Task


def _json(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return {}


def _friendship(user1, user2):
    Friendship.objects.get_or_create(user=user1, friend=user2)
    Friendship.objects.get_or_create(user=user2, friend=user1)


def _default_avatar_url():
    return '/static/avater.jpeg'


def _user_dict(u):
    return {
        'id': u.id,
        'username': u.username,
        'display_name': u.display_name,
        'avatar_url': u.avatar_url or _default_avatar_url(),
        'bio': u.bio,
        'online_status': u.online_status,
        'phone': u.phone or '',
        'organization': u.organization.name if u.organization else '',
    }


def _get_registration_data(request):
    """Handle both JSON and FormData/multipart registration requests."""
    # Check content type to decide parsing strategy
    ctype = request.content_type or ''
    if 'application/json' in ctype:
        return _json(request)
    # FormData / multipart: read from request.POST directly
    return {
        'username': request.POST.get('username', ''),
        'password': request.POST.get('password', ''),
        'display_name': request.POST.get('display_name', ''),
        'phone': request.POST.get('phone', ''),
    }


@csrf_exempt
@require_http_methods(['POST'])
def register_view(request):
    data = _get_registration_data(request)
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    display_name = (data.get('display_name') or '').strip()
    if not username:
        return JsonResponse({'detail': '用户名不能为空'}, status=400)
    if not password:
        return JsonResponse({'detail': '密码不能为空'}, status=400)
    if len(username) < 3:
        return JsonResponse({'detail': '用户名至少 3 位'}, status=400)
    if len(password) < 6:
        return JsonResponse({'detail': '密码至少 6 位'}, status=400)
    phone = (data.get('phone') or '').strip()
    try:
        user = User.objects.create_user(username=username, password=password, display_name=display_name)
    except IntegrityError:
        return JsonResponse({'detail': '用户名已存在'}, status=400)
    if phone:
        # Check phone uniqueness
        if User.objects.filter(phone=phone).exists():
            user.delete()
            return JsonResponse({'detail': '手机号已存在'}, status=400)
        user.phone = phone
        user.save(update_fields=['phone'])
    avatar_file = request.FILES.get('avatar')
    if avatar_file:
        path = default_storage.save(f'avatars/{user.id}/{avatar_file.name}', avatar_file)
        user.avatar_url = f'/media/{path}'
    else:
        user.avatar_url = _default_avatar_url()
    user.save(update_fields=['avatar_url'])
    login(request, user)
    return JsonResponse(_user_dict(user))


@csrf_exempt
@require_http_methods(['POST'])
def login_view(request):
    data = _json(request)
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return JsonResponse({'detail': '用户名和密码不能为空'}, status=400)
    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({'detail': '用户名或密码错误'}, status=400)
    login(request, user)
    # 记住我：勾选 → 30 天；不勾选 → 浏览器会话（关闭即过期）
    if data.get('remember_me', False):
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)
    else:
        request.session.set_expiry(0)
    user.online_status = 'online'
    user.save(update_fields=['online_status'])
    return JsonResponse(_user_dict(user))


@csrf_exempt
@require_http_methods(['POST'])
def logout_view(request):
    if request.user.is_authenticated:
        request.user.online_status = 'offline'
        request.user.save(update_fields=['online_status'])
    logout(request)
    return JsonResponse({'detail': 'ok'})


@login_required
def me_view(request):
    return JsonResponse(_user_dict(request.user))


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def update_profile_view(request):
    data = _json(request)
    u = request.user
    if 'display_name' in data:
        u.display_name = (data['display_name'] or '').strip()
    if 'bio' in data:
        u.bio = (data['bio'] or '').strip()
    u.save(update_fields=['display_name', 'bio'])
    return JsonResponse(_user_dict(u))


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def update_status_view(request):
    data = _json(request)
    status = data.get('status', 'online')
    valid = [s[0] for s in User.ONLINE_STATUS]
    if status not in valid:
        return JsonResponse({'detail': 'invalid status'}, status=400)
    request.user.online_status = status
    request.user.save(update_fields=['online_status'])
    return JsonResponse({'online_status': request.user.online_status})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def change_password_view(request):
    data = _json(request)
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    if not old_pw or not new_pw:
        return JsonResponse({'detail': '密码不能为空'}, status=400)
    if len(new_pw) < 6:
        return JsonResponse({'detail': '新密码至少 6 位'}, status=400)
    if not request.user.check_password(old_pw):
        return JsonResponse({'detail': '原密码错误'}, status=400)
    request.user.set_password(new_pw)
    request.user.save()
    login(request, request.user)
    return JsonResponse({'detail': 'ok'})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def add_friend_view(request):
    data = _json(request)
    username = (data.get('username') or '').strip()
    if not username:
        return JsonResponse({'detail': '用户名不能为空'}, status=400)
    if username == request.user.username:
        return JsonResponse({'detail': '不能添加自己'}, status=400)
    try:
        receiver = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'detail': '用户不存在'}, status=404)
    if Friendship.objects.filter(user=request.user, friend=receiver).exists():
        return JsonResponse({'detail': '已经是好友了'}, status=400)
    fr, created = FriendRequest.objects.get_or_create(
        sender=request.user, receiver=receiver,
        defaults={'message': data.get('message', '')}
    )
    if not created and fr.status == 'pending':
        return JsonResponse({'detail': '申请已发送，等待对方确认'}, status=400)
    if not created:
        fr.status = 'pending'
        fr.save(update_fields=['status'])
    # Create notification for the receiver
    Notification.objects.create(
        user=receiver,
        notif_type='friend_request',
        title='好友申请',
        message=f'{request.user.display_name or request.user.username} 请求添加好友',
        related_id=fr.id,
    )
    # Real-time push via WebSocket
    from myapp.notify import notify_friend_request
    notify_friend_request(
        receiver.id, fr.id, request.user.username,
        request.user.display_name or request.user.username,
        request.user.avatar_url or '/static/avater.jpeg',
        data.get('message', ''),
    )
    return JsonResponse({'id': fr.id, 'status': fr.status})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def friend_request_action_view(request, request_id):
    data = _json(request)
    action = data.get('action')
    try:
        fr = FriendRequest.objects.get(id=request_id, receiver=request.user)
    except FriendRequest.DoesNotExist:
        return JsonResponse({'detail': 'not found'}, status=404)
    if action == 'accept':
        fr.status = 'accepted'
        fr.save(update_fields=['status'])
        _friendship(fr.sender, fr.receiver)
        Notification.objects.create(
            user=fr.sender,
            notif_type='friend_accepted',
            title='好友申请通过',
            message=f'{fr.receiver.display_name or fr.receiver.username} 已接受你的好友请求',
        )
        from myapp.notify import notify_friend_accepted
        notify_friend_accepted(fr.sender.id, fr.receiver.display_name or fr.receiver.username)
        return JsonResponse({'detail': 'accepted'})
    if action == 'reject':
        fr.status = 'rejected'
        fr.save(update_fields=['status'])
        return JsonResponse({'detail': 'rejected'})
    return JsonResponse({'detail': 'invalid action'}, status=400)


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def remove_friend_view(request, friend_id):
    try:
        friend = User.objects.get(id=friend_id)
    except User.DoesNotExist:
        return JsonResponse({'detail': 'not found'}, status=404)
    Friendship.objects.filter(user=request.user, friend=friend).delete()
    Friendship.objects.filter(user=friend, friend=request.user).delete()
    return JsonResponse({'detail': 'ok'})


@login_required
def friends_view(request):
    rows = Friendship.objects.filter(user=request.user).select_related('friend')
    pending = FriendRequest.objects.filter(receiver=request.user, status='pending').select_related('sender')
    return JsonResponse({
        'friends': [_user_dict(r.friend) for r in rows],
        'pending_requests': [
            {'id': r.id, 'sender': r.sender.username, 'display_name': r.sender.display_name,
             'avatar_url': r.sender.avatar_url or _default_avatar_url(), 'message': r.message}
            for r in pending
        ],
    })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def avatar_upload_view(request):
    file = request.FILES.get('avatar')
    if not file:
        return JsonResponse({'detail': 'missing file'}, status=400)
    path = default_storage.save(f'avatars/{request.user.id}/{file.name}', file)
    request.user.avatar_url = f'/media/{path}'
    request.user.save(update_fields=['avatar_url'])
    return JsonResponse({'avatar_url': request.user.avatar_url})


@login_required
def search_users_view(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'users': []})
    from django.db.models import Q
    users = User.objects.filter(
        Q(username__icontains=q) | Q(display_name__icontains=q)
    ).exclude(id=request.user.id)[:20]
    return JsonResponse({'users': [_user_dict(u) for u in users]})


# ===== Task Dispatch =====

@login_required
@csrf_exempt
@require_http_methods(['POST'])
def create_task_view(request):
    """Create a task and assign it to a user. Supports both JSON and FormData (with file)."""
    ctype = request.content_type or ''
    if 'application/json' in ctype:
        data = _json(request)
        title = (data.get('title') or '').strip()
        description = (data.get('description') or '').strip()
        content = (data.get('content') or '').strip()
        assignee_id = data.get('assignee_id')
        attachment_url = data.get('attachment_url', '')
        attachment_name = data.get('attachment_name', '')
    else:
        title = (request.POST.get('title') or '').strip()
        description = (request.POST.get('description') or '').strip()
        content = (request.POST.get('content') or '').strip()
        assignee_id = request.POST.get('assignee_id')
        attachment_url = ''
        attachment_name = ''
    if not title:
        return JsonResponse({'detail': '任务标题不能为空'}, status=400)
    if not assignee_id:
        return JsonResponse({'detail': '请指定处理人'}, status=400)
    try:
        assignee = User.objects.get(id=assignee_id)
    except User.DoesNotExist:
        return JsonResponse({'detail': '处理人不存在'}, status=404)
    # Handle file upload
    attachment_file = request.FILES.get('attachment')
    if attachment_file:
        path = default_storage.save(f'tasks/{request.user.id}/{attachment_file.name}', attachment_file)
        attachment_url = f'/media/{path}'
        attachment_name = attachment_file.name
    task = Task.objects.create(
        title=title,
        description=description,
        content=content,
        created_by=request.user,
        assignee=assignee,
        attachment_url=attachment_url,
        attachment_name=attachment_name,
    )
    from myapp.notify import notify_task_assigned
    notifier_name = request.user.display_name or request.user.username
    notify_task_assigned(assignee.id, task.id, title, notifier_name)
    return JsonResponse({'id': task.id, 'status': task.status})


@login_required
def list_tasks_view(request):
    """Get tasks assigned to me (as assignee)."""
    status_filter = request.GET.get('status', '')
    qs = Task.objects.filter(assignee=request.user).select_related('created_by').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    data = []
    for t in qs:
        data.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'content': t.content,
            'status': t.status,
            'created_by': t.created_by.display_name or t.created_by.username,
            'created_by_id': t.created_by.id,
            'created_by_avatar': t.created_by.avatar_url or '/static/avater.jpeg',
            'assignee_id': t.assignee.id,
            'attachment_url': t.attachment_url,
            'attachment_name': t.attachment_name,
            'created_at': t.created_at.isoformat(),
            'updated_at': t.updated_at.isoformat(),
        })
    return JsonResponse({'tasks': data})


@login_required
def list_sent_tasks_view(request):
    """Get tasks I created (as creator)."""
    status_filter = request.GET.get('status', '')
    qs = Task.objects.filter(created_by=request.user).select_related('assignee').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    data = []
    for t in qs:
        data.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'content': t.content,
            'status': t.status,
            'assignee': t.assignee.display_name or t.assignee.username,
            'assignee_id': t.assignee.id,
            'assignee_avatar': t.assignee.avatar_url or '/static/avater.jpeg',
            'attachment_url': t.attachment_url,
            'attachment_name': t.attachment_name,
            'created_at': t.created_at.isoformat(),
            'updated_at': t.updated_at.isoformat(),
        })
    return JsonResponse({'tasks': data})


@login_required
def task_detail_view(request, task_id):
    """Get detail of a single task."""
    t = get_object_or_404(Task, id=task_id)
    if request.user != t.assignee and request.user != t.created_by:
        return JsonResponse({'detail': 'forbidden'}, status=403)
    return JsonResponse({
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'content': t.content,
        'status': t.status,
        'created_by': t.created_by.display_name or t.created_by.username,
        'created_by_id': t.created_by.id,
        'created_by_avatar': t.created_by.avatar_url or '/static/avater.jpeg',
        'assignee': t.assignee.display_name or t.assignee.username,
        'assignee_id': t.assignee.id,
        'assignee_avatar': t.assignee.avatar_url or '/static/avater.jpeg',
        'attachment_url': t.attachment_url,
        'attachment_name': t.attachment_name,
        'created_at': t.created_at.isoformat(),
        'updated_at': t.updated_at.isoformat(),
    })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def update_task_status_view(request, task_id):
    """Update task status (mark complete, etc.)."""
    t = get_object_or_404(Task, id=task_id)
    if request.user != t.assignee and request.user != t.created_by:
        return JsonResponse({'detail': 'forbidden'}, status=403)
    data = _json(request)
    new_status = data.get('status', '')
    valid_statuses = [s[0] for s in Task.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({'detail': '无效的状态'}, status=400)
    t.status = new_status
    t.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'detail': 'ok', 'status': t.status})


# ===== Notifications =====

@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user, is_read=False)[:50]
    return JsonResponse({
        'notifications': [
            {
                'id': n.id,
                'type': n.notif_type,
                'title': n.title,
                'message': n.message,
                'related_id': n.related_id,
                'action_url': n.action_url,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
            }
            for n in notifs
        ],
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
    })


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def mark_notification_read_view(request):
    data = _json(request)
    notif_id = data.get('notification_id')
    if notif_id:
        Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
    else:
        Notification.objects.filter(user=request.user).update(is_read=True)
    return JsonResponse({'detail': 'ok'})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def dismiss_notification_view(request, notif_id):
    """Dismiss a notification (mark as read and it won't appear in list)."""
    Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
    return JsonResponse({'detail': 'ok'})
