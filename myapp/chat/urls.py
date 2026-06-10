from django.urls import path
from .views import (
    app_home, conversations_view, messages_view, create_conversation_view,
    send_message_view, mark_read_view, delete_conversation_view,
    revoke_message_view, conversation_member_manage_view,
    search_view, presence_view, archive_conversation_view,
    restore_conversation_view,
)

urlpatterns = [
    path('conversations/', conversations_view),
    path('conversations/create/', create_conversation_view),
    path('conversations/<int:conversation_id>/messages/', messages_view),
    path('conversations/<int:conversation_id>/messages/send/', send_message_view),
    path('conversations/<int:conversation_id>/messages/<int:message_id>/revoke/', revoke_message_view),
    path('conversations/<int:conversation_id>/read/', mark_read_view),
    path('conversations/<int:conversation_id>/delete/', delete_conversation_view),
    path('conversations/<int:conversation_id>/members/', conversation_member_manage_view),
    path('search/', search_view),
    path('conversations/<int:conversation_id>/archive/', archive_conversation_view),
    path('conversations/<int:conversation_id>/restore/', restore_conversation_view),
    path('presence/', presence_view),
]
