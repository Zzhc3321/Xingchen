from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=128, unique=True, verbose_name='机构名称')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '机构'
        verbose_name_plural = '机构'


class User(AbstractUser):
    ONLINE_STATUS = [('online', '在线'), ('away', '忙碌'), ('dnd', '请勿打扰'), ('offline', '离线')]
    display_name = models.CharField(max_length=64, blank=True, verbose_name='显示名称')
    avatar_url = models.URLField(blank=True, verbose_name='头像地址')
    bio = models.CharField(max_length=255, blank=True, verbose_name='个人简介')
    online_status = models.CharField(max_length=16, choices=ONLINE_STATUS, default='offline', verbose_name='在线状态')
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name='手机号')
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name='members', verbose_name='所属机构')

    def __str__(self):
        return self.display_name or self.username

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'


class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('accepted', '已接受'),
        ('rejected', '已拒绝'),
    ]
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests', verbose_name='发送者')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests', verbose_name='接收者')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        unique_together = ('sender', 'receiver')
        verbose_name = '好友申请'
        verbose_name_plural = '好友申请'

    def __str__(self):
        return f'{self.sender} → {self.receiver} ({self.status})'


class Notification(models.Model):
    NOTIF_TYPES = [
        ('friend_request', '好友申请'),
        ('friend_accepted', '好友申请通过'),
        ('new_message', '新消息'),
        ('group_created', '建群通知'),
        ('group_invite', '群聊邀请'),
        ('task_assigned', '任务派单'),
        ('system', '系统通知'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='用户')
    notif_type = models.CharField(max_length=32, choices=NOTIF_TYPES, verbose_name='通知类型')
    title = models.CharField(max_length=128, verbose_name='标题')
    message = models.CharField(max_length=255, blank=True, verbose_name='内容')
    related_id = models.IntegerField(null=True, blank=True, verbose_name='关联ID')
    action_url = models.CharField(max_length=500, blank=True, verbose_name='点击跳转地址')
    is_read = models.BooleanField(default=False, verbose_name='已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '通知'
        verbose_name_plural = '通知'
