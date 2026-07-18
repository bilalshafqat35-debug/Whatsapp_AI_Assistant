# Generated for initial WhatsApp AI assistant schema
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='AssistantSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auto_reply_enabled', models.BooleanField(default=True)),
                ('custom_instructions', models.TextField(default='Be helpful, concise, respectful, and reply in the language used by the contact. Support English, Urdu, and Roman Urdu.')),
                ('unavailable_message', models.CharField(default='I am currently unavailable, so my AI assistant is replying for me.', max_length=255)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Assistant settings', 'verbose_name_plural': 'Assistant settings'},
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=32, unique=True)),
                ('display_name', models.CharField(blank=True, max_length=255)),
                ('language_hint', models.CharField(blank=True, help_text='English, Urdu, or Roman Urdu', max_length=32)),
                ('human_takeover', models.BooleanField(default=False)),
                ('is_blocked', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('last_seen_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('escalated', models.BooleanField(default=False)),
                ('escalation_reason', models.CharField(blank=True, max_length=255)),
                ('last_message_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contact', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='conversation', to='assistant.contact')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('whatsapp_message_id', models.CharField(blank=True, db_index=True, max_length=128)),
                ('direction', models.CharField(choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')], max_length=16)),
                ('sender_type', models.CharField(choices=[('contact', 'Contact'), ('ai', 'AI assistant'), ('human', 'Human owner'), ('system', 'System')], max_length=16)),
                ('text', models.TextField(blank=True)),
                ('raw_payload', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='assistant.conversation')),
            ],
            options={'ordering': ['created_at']},
        ),
        migrations.AddConstraint(
            model_name='message',
            constraint=models.UniqueConstraint(condition=models.Q(('whatsapp_message_id', ''), _negated=True), fields=('whatsapp_message_id',), name='unique_whatsapp_message_id'),
        ),
    ]
