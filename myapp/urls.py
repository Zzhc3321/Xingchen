from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from myapp.views import dashboard_view, dashboard_data_view, chat_page, friends_page, profile_page, events_page, login_page, register_page, api_announcements
from myapp.views import materials_page, api_materials_list, api_materials_save, api_materials_pdf, api_materials_delete, api_materials_rename, api_materials_edit, api_materials_batch_delete, api_materials_toggle_pin, api_materials_export
from myapp.chat.views import app_home
from myapp.report_views import generate_report_view, stats_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_page, name='login'),
    path('auth/login/', login_page, name='login-page'),
    path('auth/register/', register_page, name='register-page'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/data/', dashboard_data_view, name='dashboard-data'),
    path('app/', app_home, name='app-home'),
    path('chat/', chat_page, name='chat'),
    path('friends/', friends_page, name='friends'),
    path('profile/', profile_page, name='profile'),
    path('events/', events_page, name='events'),
    path('materials/', materials_page, name='materials'),
    path('api/', include('myapp.members.urls')),
    path('api/', include('myapp.chat.urls')),
    path('api/', include('myapp.events.urls')),
    path('api/announcements/', api_announcements, name='api-announcements'),
    path('api/reports/generate/', generate_report_view, name='api-reports-generate'),
    path('api/reports/stats/', stats_view, name='api-reports-stats'),
    path('api/materials/', api_materials_list, name='api-materials-list'),
    path('api/materials/save/', api_materials_save, name='api-materials-save'),
    path('api/materials/<int:material_id>/pdf/', api_materials_pdf, name='api-materials-pdf'),
    path('api/materials/<int:material_id>/delete/', api_materials_delete, name='api-materials-delete'),
    path('api/materials/<int:material_id>/rename/', api_materials_rename, name='api-materials-rename'),
    path('api/materials/<int:material_id>/edit/', api_materials_edit, name='api-materials-edit'),
    path('api/materials/batch-delete/', api_materials_batch_delete, name='api-materials-batch-delete'),
    path('api/materials/<int:material_id>/toggle-pin/', api_materials_toggle_pin, name='api-materials-toggle-pin'),
    path('api/materials/<int:material_id>/export/', api_materials_export, name='api-materials-export'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
