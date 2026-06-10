from django.contrib import admin
from .models import Conversation, Message, ConversationReadState, ConversationMember


class ConversationMemberInline(admin.TabularInline):
    model = ConversationMember
    extra = 0
    raw_id_fields = ['user']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'conversation_type', 'created_by', 'archived', 'created_at', 'updated_at']
    list_filter = ['conversation_type', 'archived', 'created_at']
    search_fields = ['title', 'created_by__username', 'created_by__display_name']
    raw_id_fields = ['created_by', 'participants']
    inlines = [ConversationMemberInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content_preview', 'is_read', 'revoked_at', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['content', 'sender__username', 'conversation__title']
    raw_id_fields = ['conversation', 'sender', 'revoked_by']

    def content_preview(self, obj):
        return obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
    content_preview.short_description = '消息内容'


@admin.register(ConversationReadState)
class ConversationReadStateAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'user', 'last_read_at']
    search_fields = ['conversation__title', 'user__username', 'user__display_name']
    raw_id_fields = ['conversation', 'user']


@admin.register(ConversationMember)
class ConversationMemberAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'user', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['conversation__title', 'user__username', 'user__display_name']
    raw_id_fields = ['conversation', 'user']
