from django.urls import path
from .views import (
    register_view, login_view, logout_view, me_view,
    update_profile_view, update_status_view, change_password_view,
    avatar_upload_view, search_users_view,
    notifications_view, mark_notification_read_view, dismiss_notification_view,
    friend_request_view, friend_handle_view, friends_list_view, friends_pending_view,
)

urlpatterns = [
    path('auth/register/', register_view),
    path('auth/login/', login_view),
    path('auth/logout/', logout_view),
    path('auth/me/', me_view),
    path('profile/update/', update_profile_view),
    path('profile/status/', update_status_view),
    path('profile/password/', change_password_view),
    path('profile/avatar/', avatar_upload_view),
    path('users/search/', search_users_view),
    path('notifications/', notifications_view),
    path('notifications/read/', mark_notification_read_view),
    path('notifications/<int:notif_id>/dismiss/', dismiss_notification_view),
    path('friends/request/', friend_request_view),
    path('friends/handle/', friend_handle_view),
    path('friends/', friends_list_view),
    path('friends/pending/', friends_pending_view),
]
