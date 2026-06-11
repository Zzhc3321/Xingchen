import json
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Conversation, ConversationMember, ConversationReadState, Message
from myapp.members.models import User


@login_required
def app_home(request):
    # Legacy route — redirect to chat page
    from django.shortcuts import redirect
    return redirect('chat')


def _json(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return {}


def _msg_dict(m):
    return {
        'id': m.id,
        'sender': m.sender.username,
        'sender_id': m.sender.id,
        'display_name': m.sender.display_name or m.sender.username,
        'avatar_url': m.sender.avatar_url or '/static/avater.jpeg',
        'content': '' if m.revoked_at else m.content,
        'attachment_url': m.attachment_url,
        'attachment_name': m.attachment_name,
        'attachment_type': m.attachment_type,
        'created_at': m.created_at.isoformat(),
        'is_read': m.is_read,
        'revoked_at': m.revoked_at.isoformat() if m.revoked_at else None,
    }


@login_required
def conversations_view(request):
    qs = (request.user.conversations
          .filter(participants=request.user)
          .annotate(last_message_at=Max('messages__created_at'))
          .prefetch_related('participants')
          .order_by('-last_message_at', '-updated_at'))
    data = []
    for c in qs:
        unread = c.messages.exclude(sender=request.user).filter(is_read=False).count()
        last_msg = c.messages.order_by('-created_at').select_related('sender').first()
        last_content = ''
        last_sender = ''
        last_sender_id = None
        if last_msg:
            if last_msg.revoked_at:
                last_content = '[消息已撤回]'
            elif last_msg.attachment_url:
                last_content = f'[{last_msg.attachment_name or "文件"}]'
            else:
                last_msg_text = last_msg.content or ''
                last_content = last_msg_text[:100] + ('…' if len(last_msg_text) > 100 else '')
            last_sender = last_msg.sender.display_name or last_msg.sender.username
            last_sender_id = last_msg.sender.id
        data.append({
            'id': c.id,
            'type': c.conversation_type,
            'title': c.title or c.display_title(),
            'unread_count': unread,
            'last_message': last_content,
            'last_message_at': last_msg.created_at.isoformat() if last_msg else None,
            'last_sender': last_sender,
            'last_sender_id': last_sender_id,
            'archived': c.archived,
            'created_by': c.created_by_id,
            'participants': [
                {'id': u.id, 'username': u.username,
                 'display_name': u.display_name or u.username,
                 'avatar_url': u.avatar_url or '/static/avater.jpeg',
                 'online_status': u.online_status}
                for u in c.participants.all()
            ],
        })
    return JsonResponse({'conversations': data})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def create_conversation_view(request):
    data = _json(request)
    ctype = data.get('type', 'direct')
    title = (data.get('title') or '').strip()
    participant_ids = data.get('participant_ids', [])

    if ctype == 'direct':
        if len(participant_ids) != 1:
            return JsonResponse({'detail': '私聊需要恰好一个参与者'}, status=400)
        peer_id = participant_ids[0]
        # Return existing direct conversation if one exists
        existing = Conversation.objects.filter(
            conversation_type='direct', participants=request.user
        ).filter(participants__id=peer_id).first()
        if existing:
            return JsonResponse({'id': existing.id})

    conv = Conversation.objects.create(conversation_type=ctype, title=title, created_by=request.user)
    participants = [request.user]
    for pid in participant_ids:
        try:
            participants.append(User.objects.get(id=pid))
        except User.DoesNotExist:
            return JsonResponse({'detail': f'用户 {pid} 不存在'}, status=404)
    # Add AI robot by default for group conversations
    if ctype == 'group':
        from myapp.ai_robot import get_robot_user
        robot = get_robot_user()
        if robot:
            participants.append(robot)
    conv.participants.add(*participants)
    for u in participants:
        ConversationMember.objects.get_or_create(
            conversation=conv, user=u,
            defaults={'role': 'admin' if u == request.user else 'member'}
        )
    if ctype == 'group':
        # Notify all added members
        from myapp.notify import notify_group_invite
        sender_name = request.user.display_name or request.user.username
        for u in participants:
            if u != request.user:
                notify_group_invite(u.id, conv.id, title or '群聊', sender_name)
    if ctype == 'direct' and len(participants) == 2 and not title:
        peer = [p for p in participants if p != request.user][0]
        conv.title = peer.display_name or peer.username
        conv.save(update_fields=['title'])
    return JsonResponse({'id': conv.id})


@login_required
def messages_view(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conv.participants.all():
        return JsonResponse({'detail': 'forbidden'}, status=403)
    msgs = conv.messages.select_related('sender', 'revoked_by').order_by('created_at')
    ConversationReadState.objects.update_or_create(
        conversation=conv, user=request.user,
        defaults={'last_read_at': timezone.now()}
    )
    conv.messages.exclude(sender=request.user).update(is_read=True)
    return JsonResponse({'messages': [_msg_dict(m) for m in msgs]})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def send_message_view(request, conversation_id):
    """REST endpoint for sending messages (used for file attachments)."""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    conv = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conv.participants.all():
        return JsonResponse({'detail': 'forbidden'}, status=403)

    content = ''
    attachment_url = ''
    attachment_name = ''
    attachment_type = ''

    if request.FILES.get('file'):
        f = request.FILES['file']
        path = default_storage.save(f'attachments/{f.name}', f)
        attachment_url = f'/media/{path}'
        attachment_name = f.name
        attachment_type = f.content_type
    else:
        data = _json(request)
        content = (data.get('content') or '').strip()
        attachment_url = data.get('attachment_url', '')
        attachment_name = data.get('attachment_name', '')
        attachment_type = data.get('attachment_type', '')

    if not content and not attachment_url:
        return JsonResponse({'detail': '消息不能为空'}, status=400)

    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        content=content,
        attachment_url=attachment_url,
        attachment_name=attachment_name,
        attachment_type=attachment_type,
    )
    ConversationReadState.objects.update_or_create(
        conversation=conv, user=request.user,
        defaults={'last_read_at': timezone.now()}
    )

    payload = _msg_dict(msg)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{conversation_id}',
        {'type': 'chat_message', 'message': payload}
    )
    # Real-time notification to other participants
    from myapp.notify import notify_new_message
    sender_name = request.user.display_name or request.user.username
    for p in conv.participants.exclude(id=request.user.id):
        notify_new_message(
            p.id, conv.id, conv.title or '会话',
            sender_name, content or '[文件]',
            conv.conversation_type,
        )

    # Check for @星辰AI助手 in REST endpoint (fallback when WS is unavailable)
    if content and conv.conversation_type == 'group':
        from myapp.ai_robot import message_mentions_robot, call_ai_api_sync, get_robot_user
        if message_mentions_robot(content):
            robot = get_robot_user()
            if robot:
                # Fetch last 20 messages
                recent = Message.objects.filter(conversation=conv).exclude(content='').select_related('sender').order_by('-created_at')[:20]
                history_lines = []
                for m in reversed(recent):
                    name = m.sender.display_name or m.sender.username
                    history_lines.append(f"{name}: {m.content}")
                history_text = '\n'.join(history_lines)

                # Call API in background thread
                import threading
                from django.db import close_old_connections
                def reply_async():
                    close_old_connections()
                    input_file = attachment_url if attachment_url else None
                    reply = call_ai_api_sync(content, history_text, input_file=input_file)
                    if reply:
                        from myapp.chat.models import Message as Msg
                        robot_msg = Msg.objects.create(conversation=conv, sender=robot, content=reply)
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f'chat_{conversation_id}',
                            {'type': 'chat_message', 'message': {
                                'id': robot_msg.id,
                                'sender': '星辰AI助手',
                                'sender_id': robot.id,
                                'display_name': '星辰AI助手',
                                'avatar_url': robot.avatar_url or '/static/avater.jpeg',
                                'content': reply,
                                'attachment_url': '', 'attachment_name': '', 'attachment_type': '',
                                'created_at': robot_msg.created_at.isoformat(),
                                'is_read': False, 'revoked_at': None,
                            }}
                        )
                threading.Thread(target=reply_async, daemon=True).start()

    return JsonResponse(payload)


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def mark_read_view(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    ConversationReadState.objects.update_or_create(
        conversation=conv, user=request.user,
        defaults={'last_read_at': timezone.now()}
    )
    conv.messages.exclude(sender=request.user).update(is_read=True)
    return JsonResponse({'detail': 'ok'})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def delete_conversation_view(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    conv.participants.remove(request.user)
    ConversationMember.objects.filter(conversation=conv, user=request.user).delete()
    return JsonResponse({'detail': 'ok'})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def revoke_message_view(request, conversation_id, message_id):
    m = get_object_or_404(Message, id=message_id, conversation__id=conversation_id)
    if m.sender != request.user:
        return JsonResponse({'detail': '只能撤回自己的消息'}, status=403)
    if timezone.now() - m.created_at > timedelta(minutes=2):
        return JsonResponse({'detail': '超过撤回时限（2分钟）'}, status=400)
    m.revoked_at = timezone.now()
    m.revoked_by = request.user
    m.content = ''
    m.save(update_fields=['revoked_at', 'revoked_by', 'content', 'updated_at'])
    return JsonResponse({'detail': 'ok'})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def conversation_member_manage_view(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    data = _json(request)
    action = data.get('action')
    user_id = data.get('user_id')
    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'detail': 'user not found'}, status=404)
    if action == 'invite':
        conv.participants.add(target)
        ConversationMember.objects.get_or_create(conversation=conv, user=target)
        from myapp.notify import notify_group_invite
        sender_name = request.user.display_name or request.user.username
        notify_group_invite(target.id, conv.id, conv.title or '群聊', sender_name)
        return JsonResponse({'detail': 'invited'})
    if action == 'remove':
        if conv.created_by != request.user:
            return JsonResponse({'detail': '只有群主可以移除成员'}, status=403)
        conv.participants.remove(target)
        ConversationMember.objects.filter(conversation=conv, user=target).delete()
        return JsonResponse({'detail': 'removed'})
    return JsonResponse({'detail': 'invalid action'}, status=400)


@login_required
def search_view(request):
    data = _json(request)
    q = (data.get('q') or '').strip()
    if len(q) < 2:
        return JsonResponse({'users': [], 'messages': []})
    users = User.objects.filter(
        Q(username__icontains=q) | Q(display_name__icontains=q)
    ).exclude(id=request.user.id)[:20]
    # Only search messages in conversations the user participates in
    user_conv_ids = request.user.conversations.values_list('id', flat=True)
    messages = Message.objects.filter(
        content__icontains=q,
        conversation_id__in=user_conv_ids,
    ).select_related('conversation', 'sender')[:20]
    return JsonResponse({
        'users': [{'id': u.id, 'username': u.username,
                   'display_name': u.display_name, 'avatar_url': u.avatar_url,
                   'phone': u.phone or '', 'organization': u.organization.name if u.organization else ''}
                  for u in users],
        'messages': [{'id': m.id, 'content': m.content,
                      'sender': m.sender.username,
                      'conversation_id': m.conversation_id}
                     for m in messages],
    })


@login_required
def presence_view(request):
    return JsonResponse({'online_users': []})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def archive_conversation_view(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    data = _json(request)
    archived = data.get('archived', True)
    conv.archived = archived
    conv.save(update_fields=['archived'])
    return JsonResponse({'detail': 'ok'})


@login_required
@csrf_exempt
@require_http_methods(['POST'])
def restore_conversation_view(request, conversation_id):
    """Restore an archived conversation. Only the creator can restore."""
    conv = get_object_or_404(Conversation, id=conversation_id)
    if request.user != conv.created_by:
        return JsonResponse({'detail': '只有会话创建者可以恢复'}, status=403)
    conv.archived = False
    conv.save(update_fields=['archived'])
    return JsonResponse({'detail': 'ok'})
