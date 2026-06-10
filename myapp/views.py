from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Announcement


def _render(request, template, nav=None):
    return render(request, template, {'active_nav': nav})


@login_required
def dashboard_view(request):
    return _render(request, 'dashboard.html', 'dashboard')


@login_required
def chat_page(request):
    return _render(request, 'chat.html', 'chat')


@login_required
def friends_page(request):
    return _render(request, 'friends.html', 'friends')


@login_required
def profile_page(request):
    return _render(request, 'profile.html', 'profile')


@login_required
def events_page(request):
    return _render(request, 'events.html', 'events')


def login_page(request):
    return render(request, 'login.html')


def register_page(request):
    return render(request, 'register.html')


def api_announcements(request):
    """API: 获取通知公告列表"""
    qs = Announcement.objects.filter(is_active=True)
    return JsonResponse({
        'announcements': [{
            'id': a.id,
            'title': a.title,
            'content': a.content,
            'is_pinned': a.is_pinned,
            'created_at': a.created_at.isoformat(),
        } for a in qs],
    })
