import json
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import User, Notification, FriendRequest


def _json(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return {}


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
    ctype = request.content_type or ''
    if 'application/json' in ctype:
        return _json(request)
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
    Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
    return JsonResponse({'detail': 'ok'})


# ===== Friends =====


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def friend_request_view(request):
    """Send a friend request to another user."""
    data = _json(request)
    receiver_id = data.get('receiver_id')
    if not receiver_id:
        return JsonResponse({'detail': '缺少 receiver_id'}, status=400)
    if receiver_id == request.user.id:
        return JsonResponse({'detail': '不能添加自己为好友'}, status=400)
    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return JsonResponse({'detail': '用户不存在'}, status=404)
    existing = FriendRequest.objects.filter(
        Q(sender=request.user, receiver=receiver) | Q(sender=receiver, receiver=request.user)
    ).first()
    if existing:
        if existing.status == 'accepted':
            return JsonResponse({'detail': '已经是好友了'}, status=400)
        if existing.status == 'pending':
            return JsonResponse({'detail': '已发送过好友申请'}, status=400)
        # If rejected before, allow re-sending by updating
        existing.status = 'pending'
        existing.save(update_fields=['status'])
        return JsonResponse({'detail': '好友申请已重新发送'})
    fr = FriendRequest.objects.create(sender=request.user, receiver=receiver)
    # Send notification
    from myapp.notify import notify_friend_request
    notify_friend_request(
        receiver.id, fr.id,
        request.user.username,
        request.user.display_name or request.user.username,
        request.user.avatar_url or '',
    )
    return JsonResponse({'detail': '好友申请已发送', 'request_id': fr.id})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def friend_handle_view(request):
    """Accept or reject a friend request."""
    data = _json(request)
    request_id = data.get('request_id')
    action = data.get('action')  # 'accept' or 'reject'
    if not request_id or action not in ('accept', 'reject'):
        return JsonResponse({'detail': '参数无效'}, status=400)
    try:
        fr = FriendRequest.objects.get(id=request_id, receiver=request.user, status='pending')
    except FriendRequest.DoesNotExist:
        return JsonResponse({'detail': '申请不存在或已处理'}, status=404)
    if action == 'accept':
        fr.status = 'accepted'
        fr.save(update_fields=['status'])
        # Notify the sender
        from myapp.notify import notify_friend_accepted
        notify_friend_accepted(
            fr.sender_id,
            request.user.display_name or request.user.username,
        )
        return JsonResponse({'detail': '已接受好友申请'})
    else:
        fr.status = 'rejected'
        fr.save(update_fields=['status'])
        return JsonResponse({'detail': '已拒绝好友申请'})


@login_required
def friends_list_view(request):
    """List all accepted friends."""
    sent = FriendRequest.objects.filter(
        sender=request.user, status='accepted'
    ).select_related('receiver')
    received = FriendRequest.objects.filter(
        receiver=request.user, status='accepted'
    ).select_related('sender')
    friends = []
    for fr in sent:
        u = fr.receiver
        friends.append(_user_dict(u))
    for fr in received:
        u = fr.sender
        friends.append(_user_dict(u))
    # Deduplicate by id
    seen = set()
    unique = []
    for f in friends:
        if f['id'] not in seen:
            seen.add(f['id'])
            unique.append(f)
    return JsonResponse({'friends': unique})


@login_required
def friends_pending_view(request):
    """List pending friend requests (inbox and sent)."""
    inbox = FriendRequest.objects.filter(
        receiver=request.user, status='pending'
    ).select_related('sender')
    sent = FriendRequest.objects.filter(
        sender=request.user, status='pending'
    ).select_related('receiver')
    return JsonResponse({
        'incoming': [{
            'id': fr.id,
            'sender_id': fr.sender.id,
            'sender': fr.sender.username,
            'display_name': fr.sender.display_name or fr.sender.username,
            'avatar_url': fr.sender.avatar_url or '/static/avater.jpeg',
            'created_at': fr.created_at.isoformat(),
        } for fr in inbox],
        'sent': [{
            'id': fr.id,
            'receiver_id': fr.receiver.id,
            'receiver': fr.receiver.username,
            'display_name': fr.receiver.display_name or fr.receiver.username,
            'avatar_url': fr.receiver.avatar_url or '/static/avater.jpeg',
            'created_at': fr.created_at.isoformat(),
        } for fr in sent],
    })
