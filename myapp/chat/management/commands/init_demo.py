from django.core.management.base import BaseCommand
from myapp.members.models import User
from myapp.chat.models import Conversation, Message
from myapp.ai_robot import get_robot_user


class Command(BaseCommand):
    help = 'Initialize demo data for chat app'

    def handle(self, *args, **options):
        alice, _ = User.objects.get_or_create(username='alice', defaults={'display_name': 'Alice'})
        bob, _ = User.objects.get_or_create(username='bob', defaults={'display_name': 'Bob'})
        if not alice.has_usable_password():
            alice.set_password('12345678')
            alice.save()
        if not bob.has_usable_password():
            bob.set_password('12345678')
            bob.save()
        conv, _ = Conversation.objects.get_or_create(conversation_type='direct', created_by=alice, title='')
        conv.participants.set([alice, bob])
        Message.objects.get_or_create(conversation=conv, sender=alice, content='你好，欢迎使用星辰协同平台')
        # Ensure AI robot user exists
        robot = get_robot_user()
        if robot:
            self.stdout.write(self.style.SUCCESS(f'AI robot user ready (id={robot.id})'))
        self.stdout.write(self.style.SUCCESS('Demo data initialized'))
