import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    """Global notification WebSocket — one connection per user, receives
    real-time pushes for friend requests, friend accepted, new messages, etc."""

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.group_name = f'notify_user_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        # Mark user as online when WebSocket connects
        await self._set_online_status('online')

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @sync_to_async
    def _set_online_status(self, status):
        """Update the user's online_status in DB."""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            User.objects.filter(id=self.user.id).update(online_status=status)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        """Client can send a ping to keep alive."""
        try:
            data = json.loads(text_data or '{}')
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            pass

    async def _send(self, payload):
        """Send JSON payload to the WebSocket client."""
        await self.send(text_data=json.dumps(payload))

    # ---- Event handlers (called by channel_layer.group_send) ----

    async def notif_friend_request(self, event):
        await self._send({
            'type': 'friend_request',
            'id': event.get('id'),
            'title': event.get('title', '好友申请'),
            'message': event.get('message', ''),
            'notif_type': 'friend_request',
            'action_url': event.get('action_url', '/friends/'),
            'created_at': event.get('created_at', ''),
        })

    async def notif_friend_accepted(self, event):
        await self._send({
            'type': 'friend_accepted',
            'title': event.get('title', '好友申请通过'),
            'message': event.get('message', ''),
            'notif_type': 'friend_accepted',
            'action_url': event.get('action_url', '/friends/'),
            'created_at': event.get('created_at', ''),
        })

    async def notif_new_message(self, event):
        await self._send({
            'type': 'new_message',
            'id': event.get('id'),
            'title': event.get('title', '新消息'),
            'message': event.get('message', ''),
            'notif_type': 'new_message',
            'related_id': event.get('related_id'),
            'action_url': event.get('action_url', ''),
            'created_at': event.get('created_at', ''),
        })

    async def notif_group_created(self, event):
        await self._send({
            'type': 'group_created',
            'title': event.get('title', '建群通知'),
            'message': event.get('message', ''),
            'notif_type': 'group_created',
            'related_id': event.get('related_id'),
            'action_url': event.get('action_url', ''),
            'created_at': event.get('created_at', ''),
        })

    async def notif_group_invite(self, event):
        await self._send({
            'type': 'group_invite',
            'title': event.get('title', '群聊邀请'),
            'message': event.get('message', ''),
            'notif_type': 'group_invite',
            'related_id': event.get('related_id'),
            'action_url': event.get('action_url', ''),
            'created_at': event.get('created_at', ''),
        })

    async def notif_task_assigned(self, event):
        await self._send({
            'type': 'task_assigned',
            'title': event.get('title', '新任务派单'),
            'message': event.get('message', ''),
            'notif_type': 'task_assigned',
            'related_id': event.get('related_id'),
            'action_url': event.get('action_url', ''),
            'created_at': event.get('created_at', ''),
        })

    async def notif_system(self, event):
        await self._send({
            'type': 'system',
            'title': event.get('title', '系统通知'),
            'message': event.get('message', ''),
            'notif_type': 'system',
            'action_url': event.get('action_url', ''),
            'created_at': event.get('created_at', ''),
        })

    async def notif_unread_count(self, event):
        await self._send({
            'type': 'unread_update',
            'unread_count': event.get('unread_count', 0),
            'friend_request_count': event.get('friend_request_count', 0),
        })
