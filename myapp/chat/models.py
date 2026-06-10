from django.conf import settings
from django.db import models


class Conversation(models.Model):
    CONV_TYPES = [('direct', 'direct'), ('group', 'group')]
    conversation_type = models.CharField(max_length=16, choices=CONV_TYPES, verbose_name='会话类型')
    title = models.CharField(max_length=128, blank=True, verbose_name='标题')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_conversations', verbose_name='创建者')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations', verbose_name='参与者')
    archived = models.BooleanField(default=False, verbose_name='已归档')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def display_title(self):
        if self.title:
            return self.title
        if self.conversation_type == 'direct':
            names = [p.display_name or p.username for p in self.participants.all() if p != self.created_by]
            return names[0] if names else '私聊'
        return '群聊'

    class Meta:
        verbose_name = '会话'
        verbose_name_plural = '会话'


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name='所属会话')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='发送者')
    content = models.TextField(blank=True, verbose_name='内容')
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True, verbose_name='附件')
    attachment_name = models.CharField(max_length=255, blank=True, verbose_name='附件名称')
    attachment_type = models.CharField(max_length=64, blank=True, verbose_name='附件类型')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_read = models.BooleanField(default=False, verbose_name='已读')
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name='撤回时间')
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='revoked_messages', verbose_name='撤回者')
    attachment_url = models.CharField(max_length=500, blank=True, verbose_name='附件地址')

    class Meta:
        verbose_name = '消息'
        verbose_name_plural = '消息'


class ConversationReadState(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='read_states', verbose_name='会话')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversation_read_states', verbose_name='用户')
    last_read_at = models.DateTimeField(null=True, blank=True, verbose_name='最后阅读时间')

    class Meta:
        unique_together = ('conversation', 'user')
        verbose_name = '已读状态'
        verbose_name_plural = '已读状态'


class ConversationMember(models.Model):
    ROLE_CHOICES = [('member', 'member'), ('admin', 'admin')]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='memberships', verbose_name='会话')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversation_memberships', verbose_name='用户')
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default='member', verbose_name='角色')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='加入时间')

    class Meta:
        unique_together = ('conversation', 'user')
        verbose_name = '会话成员'
        verbose_name_plural = '会话成员'
