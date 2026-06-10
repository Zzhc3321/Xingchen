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
