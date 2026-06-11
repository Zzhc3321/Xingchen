from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Organization, User, Notification, FriendRequest


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'member_count', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = '成员数'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'display_name', 'phone', 'organization', 'online_status', 'is_active', 'date_joined']
    list_filter = ['online_status', 'is_active', 'is_staff', 'organization', 'date_joined']
    search_fields = ['username', 'display_name', 'phone']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('附加信息', {'fields': ('display_name', 'avatar_url', 'bio', 'online_status', 'phone', 'organization')}),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'notif_type', 'title', 'is_read', 'created_at']
    list_filter = ['notif_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    raw_id_fields = ['user']


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'receiver', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['sender__username', 'receiver__username']
    raw_id_fields = ['sender', 'receiver']
