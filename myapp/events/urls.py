from django.urls import path
from .views import (
    events_view, create_event_view, event_detail_view, create_event_group_view,
    archive_event_view, restore_event_view, tag_list_view, event_tags_view,
    memo_list_view, memo_create_view, memo_delete_view, memo_dates_view,
)

urlpatterns = [
    path('events/', events_view),
    path('events/create/', create_event_view),
    path('events/<int:event_id>/', event_detail_view),
    path('events/<int:event_id>/create-group/', create_event_group_view),
    path('events/<int:event_id>/archive/', archive_event_view),
    path('events/<int:event_id>/restore/', restore_event_view),
    path('events/<int:event_id>/tags/', event_tags_view),
    path('tags/', tag_list_view),
    path('memos/', memo_list_view),
    path('memos/create/', memo_create_view),
    path('memos/<int:memo_id>/delete/', memo_delete_view),
    path('memos/dates/', memo_dates_view),
]
