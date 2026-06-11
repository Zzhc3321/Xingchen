from django.conf import settings
from django.db import models
from django.utils import timezone


class Announcement(models.Model):
    """通知公告"""
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    is_pinned = models.BooleanField('置顶', default=False)
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '通知公告'
        verbose_name_plural = '通知公告'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title


class SavedReport(models.Model):
    REPORT_TYPES = [
        ('daily', '日报'),
        ('weekly', '周报'),
        ('archive_summary', '归档总结'),
        ('user_doc', '我的文档'),
    ]
    SOURCE_CHOICES = [
        ('report_generator', '报告生成器'),
        ('group_archive', '群聊归档'),
        ('user_save', '用户保存'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_reports', verbose_name='所属用户')
    title = models.CharField(max_length=256, verbose_name='标题')
    report_type = models.CharField(max_length=32, choices=REPORT_TYPES, default='daily', verbose_name='报告类型')
    content = models.TextField(verbose_name='内容')
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, default='report_generator', verbose_name='来源')
    is_pinned = models.BooleanField('置顶', default=False)
    related_conv_id = models.IntegerField(null=True, blank=True, verbose_name='关联会话ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '保存的报告'
        verbose_name_plural = '保存的报告'

    def __str__(self):
        return self.title
