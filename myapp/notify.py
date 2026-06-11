"""Real-time notification helpers — push events to a user's notification WebSocket."""

import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from myapp.members.models import Notification as NotificationModel


def send_notification(user_id, event_type, **kwargs):
    """Send a real-time notification to a specific user via their WS connection."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    payload = {'type': event_type, **kwargs}
    try:
        async_to_sync(channel_layer.group_send)(
            f'notify_user_{user_id}',
            payload,
        )
    except Exception:
        pass  # channel layer not available or group empty


def save_and_notify(user_id, notif_type, title, message, related_id=None, action_url=''):
    """Save a Notification in DB and push it via WebSocket."""
    notif = NotificationModel.objects.create(
        user_id=user_id,
        notif_type=notif_type,
        title=title,
        message=message,
        related_id=related_id,
        action_url=action_url,
    )
    send_notification(
        user_id,
        'notif_' + notif_type,
        id=notif.id,
        title=title,
        message=message,
        related_id=related_id,
        notif_type=notif_type,
        action_url=action_url,
        created_at=notif.created_at.isoformat(),
    )
    return notif


def notify_friend_request(receiver_id, request_id, sender_username, sender_name, sender_avatar):
    """Notify a user about an incoming friend request."""
    save_and_notify(
        receiver_id,
        'friend_request',
        '好友申请',
        f'{sender_name} 请求添加好友',
        related_id=request_id,
        action_url='/friends/',
    )


def notify_friend_accepted(sender_id, accepter_name):
    """Notify a user that their friend request was accepted."""
    save_and_notify(
        sender_id,
        'friend_accepted',
        '好友申请通过',
        f'{accepter_name} 已接受你的好友请求',
        action_url='/friends/',
    )


def notify_new_message(user_id, conversation_id, conversation_title, sender_name, content, conversation_type):
    """Notify a single user about a new message in a conversation."""
    preview = content[:200] if content else '[文件]'
    save_and_notify(
        user_id,
        'new_message',
        f'{sender_name} 发来消息',
        preview,
        related_id=conversation_id,
        action_url=f'/chat/?conv={conversation_id}',
    )


def notify_group_invite(user_id, group_id, group_title, inviter_name):
    """Notify a user that they were added to a group."""
    save_and_notify(
        user_id,
        'group_invite',
        '群聊邀请',
        f'{inviter_name} 邀请你加入群聊「{group_title}」',
        related_id=group_id,
        action_url=f'/chat/?conv={group_id}',
    )


