from django.conf import settings
from django.db import models


class Event(models.Model):
    CATEGORY_CHOICES = [('pre_sales', '售前事件'), ('in_sales', '售中事件'), ('after_sales', '售后事件'), ('custom', '自定义')]
    PRIORITY_CHOICES = [('high', '高'), ('medium', '中'), ('low', '低')]
    title = models.CharField(max_length=128, verbose_name='标题')
    description = models.TextField(blank=True, verbose_name='描述')
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='custom', verbose_name='分类')
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default='medium', verbose_name='优先级')
    status = models.CharField(max_length=32, default='open', verbose_name='状态')
    start_date = models.DateField(null=True, blank=True, verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='截止日期')
    contact_person = models.CharField(max_length=64, blank=True, verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='金额')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events', verbose_name='创建者')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='events', blank=True, verbose_name='参与者')
    tags = models.ManyToManyField('members.Tag', blank=True, related_name='events', verbose_name='标签')
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name='归档时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '事件'
        verbose_name_plural = '事件'


class EventGroup(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='group', verbose_name='事件')
    conversation = models.OneToOneField('chat.Conversation', on_delete=models.CASCADE, related_name='event_group', verbose_name='群聊')
    archived = models.BooleanField(default=False, verbose_name='已归档')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '事件群组'
        verbose_name_plural = '事件群组'


class CalendarMemo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_memos', verbose_name='用户')
    date = models.DateField(verbose_name='日期')
    title = models.CharField(max_length=128, verbose_name='标题')
    content = models.TextField(blank=True, verbose_name='内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = '日历备忘'
        verbose_name_plural = '日历备忘'

    def __str__(self):
        return f'{self.date.isoformat()} - {self.title}'
