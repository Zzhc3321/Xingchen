from django.urls import path
from .views import (
    register_view, login_view, logout_view, me_view,
    update_profile_view, update_status_view, change_password_view,
    add_friend_view, friend_request_action_view, remove_friend_view,
    friends_view, avatar_upload_view, search_users_view,
    notifications_view, mark_notification_read_view, dismiss_notification_view,
    create_task_view, list_tasks_view, list_sent_tasks_view,
    task_detail_view, update_task_status_view,
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
    path('friends/', friends_view),
    path('friends/add/', add_friend_view),
    path('friends/requests/<int:request_id>/', friend_request_action_view),
    path('friends/remove/<int:friend_id>/', remove_friend_view),
    path('users/search/', search_users_view),
    path('notifications/', notifications_view),
    path('notifications/read/', mark_notification_read_view),
    path('notifications/<int:notif_id>/dismiss/', dismiss_notification_view),
    path('tasks/', list_tasks_view),
    path('tasks/sent/', list_sent_tasks_view),
    path('tasks/create/', create_task_view),
    path('tasks/<int:task_id>/', task_detail_view),
    path('tasks/<int:task_id>/status/', update_task_status_view),
]
