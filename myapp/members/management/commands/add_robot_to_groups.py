"""Add the AI robot to all existing group conversations."""
from django.core.management.base import BaseCommand
from myapp.chat.models import Conversation, ConversationMember
from myapp.ai_robot import get_robot_user


class Command(BaseCommand):
    help = "Add the AI robot to all existing group conversations"

    def handle(self, *args, **options):
        robot = get_robot_user()
        if robot is None:
            self.stderr.write("AI robot user not found, run this command after migrations")
            return

        groups = Conversation.objects.filter(conversation_type='group')
        added = 0
        for g in groups:
            if robot not in g.participants.all():
                g.participants.add(robot)
                ConversationMember.objects.get_or_create(
                    conversation=g, user=robot,
                    defaults={'role': 'member'}
                )
                added += 1

        self.stdout.write(f"Added AI robot to {added} group(s) (out of {groups.count()} total)")
