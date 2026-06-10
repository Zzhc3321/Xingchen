import json
import asyncio
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from django.contrib.auth import get_user_model

from .models import Conversation, Message, ConversationReadState

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.group_name = f'chat_{self.conversation_id}'
        if not self.scope['user'].is_authenticated:
            await self.close()
            return
        if not await self.is_member():
            await self.close()
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data or '{}')
        content = (data.get('content') or '').strip()
        attachment_url = data.get('attachment_url') or ''
        attachment_name = data.get('attachment_name') or ''
        attachment_type = data.get('attachment_type') or ''
        if not content and not attachment_url:
            return
        message = await self.create_message(content, attachment_url, attachment_name, attachment_type)
        payload = {
            'type': 'chat_message',
            'message': {
                'id': message.id,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'display_name': message.sender.display_name or message.sender.username,
                'avatar_url': message.sender.avatar_url or '/static/avater.jpeg',
                'content': message.content,
                'attachment_url': message.attachment_url,
                'attachment_name': message.attachment_name,
                'attachment_type': message.attachment_type,
                'created_at': message.created_at.isoformat(),
                'is_read': False,
                'revoked_at': None,
            }
        }
        await self.channel_layer.group_send(self.group_name, payload)

        # Notify other participants in real-time about new message
        from asgiref.sync import sync_to_async
        from myapp.notify import notify_new_message
        notify_sync = sync_to_async(notify_new_message)
        conv = await self.get_conversation()
        if conv:
            sender_name = self.scope['user'].display_name or self.scope['user'].username
            for participant in await self.get_participants(conv):
                if participant.id != self.scope['user'].id:
                    await notify_sync(
                        participant.id, conv.id, conv.title or '会话',
                        sender_name, content or '[文件]',
                        conv.conversation_type,
                    )

        # Check if the message mentions @星辰AI助手 and trigger AI response
        if conv and content and conv.conversation_type == 'group':
            import logging
            logging.getLogger('ai_robot').info(f"Group message from {sender_name}: {content[:50]}")
            asyncio.ensure_future(self._handle_ai_mention(conv, content, sender_name, attachment_url))

    async def _handle_ai_mention(self, conv, user_content, sender_name, attachment_url=''):
        """Detect @星辰AI助手, fetch history, call API, and broadcast reply."""
        import logging
        logger = logging.getLogger('ai_robot')

        try:
            from myapp.ai_robot import message_mentions_robot, call_ai_api_async, ROBOT_DISPLAY_NAME

            if not message_mentions_robot(user_content):
                logger.info("Message does not mention robot, skipping")
                return

            logger.info("Robot mentioned! Fetching history and calling API...")

            # Fetch last 20 messages from this conversation
            recent_messages = await self._get_recent_messages(conv, 20)

            # Build conversation history string
            history_lines = []
            for m in recent_messages:
                name = m.sender.display_name or m.sender.username
                history_lines.append(f"{name}: {m.content}")

            history_text = '\n'.join(history_lines)
            input_text = user_content

            logger.info(f"Calling API with input={input_text[:50]}...")

            # Call external API (with optional file URL)
            input_file = attachment_url if attachment_url else None
            reply = await call_ai_api_async(input_text, history_text, input_file=input_file)
            if not reply:
                logger.warning("API returned empty reply")
                return

            logger.info(f"Got reply: {reply[:50]}...")

            # Post reply as AI robot message
            result = await self._create_robot_message(conv, reply)
            if result is None or result[0] is None:
                logger.warning("Failed to create robot message (robot user missing?)")
                return
            robot_msg, robot_avatar = result

            robot_payload = {
                'type': 'chat_message',
                'message': {
                    'id': robot_msg.id,
                    'sender': ROBOT_DISPLAY_NAME,
                    'sender_id': robot_msg.sender_id,
                    'display_name': ROBOT_DISPLAY_NAME,
                    'avatar_url': robot_avatar or '/static/avater.jpeg',
                    'content': reply,
                    'attachment_url': '',
                    'attachment_name': '',
                    'attachment_type': '',
                    'created_at': robot_msg.created_at.isoformat(),
                    'is_read': False,
                    'revoked_at': None,
                }
            }
            await self.channel_layer.group_send(self.group_name, robot_payload)
            logger.info("Robot reply sent to group")
        except Exception as e:
            logger.error(f"AI robot handler failed: {e}", exc_info=True)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    @sync_to_async
    def is_member(self):
        return Conversation.objects.filter(
            id=self.conversation_id, participants=self.scope['user']
        ).exists()

    @sync_to_async
    def get_conversation(self):
        try:
            return Conversation.objects.get(id=self.conversation_id)
        except Conversation.DoesNotExist:
            return None

    @sync_to_async
    def get_participants(self, conv):
        return list(conv.participants.all())

    @sync_to_async
    def create_message(self, content, attachment_url, attachment_name, attachment_type):
        conv = Conversation.objects.get(id=self.conversation_id)
        msg = Message.objects.create(
            conversation=conv,
            sender=self.scope['user'],
            content=content,
            attachment_url=attachment_url,
            attachment_name=attachment_name,
            attachment_type=attachment_type,
        )
        ConversationReadState.objects.update_or_create(
            conversation=conv,
            user=self.scope['user'],
            defaults={'last_read_at': timezone.now()}
        )
        return msg

    @sync_to_async
    def _get_recent_messages(self, conv, limit=20):
        """Fetch the most recent messages for a conversation."""
        return list(
            Message.objects.filter(conversation=conv)
            .exclude(content='')
            .select_related('sender')
            .order_by('-created_at')[:limit]
        )

    @sync_to_async
    def _create_robot_message(self, conv, content):
        """Create a message as the AI robot in the given conversation.
        Returns (message, robot_avatar_url) or None."""
        from myapp.ai_robot import get_robot_user
        robot = get_robot_user()
        if robot is None:
            return None
        msg = Message.objects.create(
            conversation=conv,
            sender=robot,
            content=content,
        )
        # Access sender info while still in sync context to avoid lazy-load in async
        return msg, robot.avatar_url or '/static/avater.jpeg'
