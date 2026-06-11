from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from myapp.views import dashboard_view, chat_page, login_page, register_page, api_announcements, friends_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_page, name='login'),
    path('auth/login/', login_page, name='login-page'),
    path('auth/register/', register_page, name='register-page'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('chat/', chat_page, name='chat'),
    path('friends/', friends_page, name='friends'),
    path('api/', include('myapp.members.urls')),
    path('api/', include('myapp.chat.urls')),
    path('api/announcements/', api_announcements, name='api-announcements'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
