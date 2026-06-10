from django.contrib import admin
from .models import Event, EventGroup


class EventGroupInline(admin.StackedInline):
    model = EventGroup
    extra = 0
    raw_id_fields = ['conversation']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'status', 'created_by', 'has_group', 'created_at', 'updated_at']
    list_filter = ['category', 'status', 'created_at']
    search_fields = ['title', 'description', 'created_by__username', 'created_by__display_name']
    raw_id_fields = ['created_by', 'participants']
    inlines = [EventGroupInline]

    def has_group(self, obj):
        return hasattr(obj, 'group')
    has_group.short_description = '已建群'
    has_group.boolean = True


@admin.register(EventGroup)
class EventGroupAdmin(admin.ModelAdmin):
    list_display = ['event', 'conversation', 'archived', 'created_at']
    list_filter = ['archived', 'created_at']
    search_fields = ['event__title', 'conversation__title']
    raw_id_fields = ['event', 'conversation']
