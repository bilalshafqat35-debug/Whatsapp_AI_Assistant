from django.db import models
from django.utils import timezone


class AssistantSettings(models.Model):
    auto_reply_enabled = models.BooleanField(default=True)
    custom_instructions = models.TextField(default='Be helpful, concise, respectful, and reply in the language used by the contact. Support English, Urdu, and Roman Urdu.')
    unavailable_message = models.CharField(max_length=255, default='I am currently unavailable, so my AI assistant is replying for me.')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Assistant settings'
        verbose_name_plural = 'Assistant settings'

    def __str__(self):
        return 'Assistant settings'

    @classmethod
    def singleton(cls):
        return cls.objects.get_or_create(pk=1)[0]


class Contact(models.Model):
    phone_number = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    language_hint = models.CharField(max_length=32, blank=True, help_text='English, Urdu, or Roman Urdu')
    human_takeover = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.phone_number


class Conversation(models.Model):
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, related_name='conversation')
    is_active = models.BooleanField(default=True)
    escalated = models.BooleanField(default=False)
    escalation_reason = models.CharField(max_length=255, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_escalated(self, reason):
        self.escalated = True
        self.escalation_reason = reason[:255]
        self.save(update_fields=['escalated', 'escalation_reason', 'updated_at'])

    def __str__(self):
        return f'Conversation with {self.contact}'


class Message(models.Model):
    class Direction(models.TextChoices):
        INBOUND = 'inbound', 'Inbound'
        OUTBOUND = 'outbound', 'Outbound'

    class SenderType(models.TextChoices):
        CONTACT = 'contact', 'Contact'
        AI = 'ai', 'AI assistant'
        HUMAN = 'human', 'Human owner'
        SYSTEM = 'system', 'System'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    whatsapp_message_id = models.CharField(max_length=128, blank=True, db_index=True)
    direction = models.CharField(max_length=16, choices=Direction.choices)
    sender_type = models.CharField(max_length=16, choices=SenderType.choices)
    text = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']
        constraints = [models.UniqueConstraint(fields=['whatsapp_message_id'], condition=~models.Q(whatsapp_message_id=''), name='unique_whatsapp_message_id')]

    def __str__(self):
        return f'{self.direction}: {self.text[:40]}'
