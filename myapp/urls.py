from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from myapp.views import dashboard_view, chat_page, friends_page, profile_page, events_page, login_page, register_page, api_announcements
from myapp.chat.views import app_home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_page, name='login'),
    path('auth/login/', login_page, name='login-page'),
    path('auth/register/', register_page, name='register-page'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('app/', app_home, name='app-home'),
    path('chat/', chat_page, name='chat'),
    path('friends/', friends_page, name='friends'),
    path('profile/', profile_page, name='profile'),
    path('events/', events_page, name='events'),
    path('api/', include('myapp.members.urls')),
    path('api/', include('myapp.chat.urls')),
    path('api/', include('myapp.events.urls')),
    path('api/announcements/', api_announcements, name='api-announcements'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
