from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('members', '0001_initial'),
    ]
    operations = [
        migrations.AddField(
            model_name='user',
            name='online_status',
            field=models.CharField(
                choices=[('online', '在线'), ('away', '忙碌'), ('dnd', '请勿打扰'), ('offline', '离线')],
                default='online',
                max_length=16,
            ),
        ),
    ]
