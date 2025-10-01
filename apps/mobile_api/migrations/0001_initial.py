# Generated manually for mobile_api models

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MobileDevice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('device_id', models.CharField(help_text='Unique device identifier', max_length=255, unique=True)),
                ('platform', models.CharField(choices=[('ios', 'iOS'), ('android', 'Android'), ('web', 'Web')], max_length=10)),
                ('fcm_token', models.TextField(blank=True, help_text='Firebase Cloud Messaging token')),
                ('app_version', models.CharField(blank=True, max_length=20)),
                ('os_version', models.CharField(blank=True, max_length=20)),
                ('device_model', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('last_seen', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mobile_devices', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Mobile Device',
                'verbose_name_plural': 'Mobile Devices',
            },
        ),
        migrations.CreateModel(
            name='SyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_type', models.CharField(choices=[('initial', 'Initial Sync'), ('incremental', 'Incremental Sync'), ('upload', 'Data Upload'), ('download', 'Data Download')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('failed', 'Failed'), ('partial', 'Partial')], default='pending', max_length=20)),
                ('total_items', models.PositiveIntegerField(default=0)),
                ('processed_items', models.PositiveIntegerField(default=0)),
                ('failed_items', models.PositiveIntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
                ('sync_data', models.JSONField(blank=True, help_text='Additional sync metadata', null=True)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_logs', to='mobile_api.mobiledevice')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sync Log',
                'verbose_name_plural': 'Sync Logs',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='RefreshToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=255, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('is_revoked', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refresh_tokens', to='mobile_api.mobiledevice')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refresh_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Refresh Token',
                'verbose_name_plural': 'Refresh Tokens',
            },
        ),
        migrations.AddConstraint(
            model_name='mobiledevice',
            constraint=models.UniqueConstraint(fields=('user', 'device_id'), name='unique_user_device'),
        ),
    ]