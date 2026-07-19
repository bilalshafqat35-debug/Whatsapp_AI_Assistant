from django.contrib import admin
from .models import AssistantSettings, Contact, Conversation, Message, ReplyExample


@admin.register(AssistantSettings)
class AssistantSettingsAdmin(admin.ModelAdmin):
    list_display = ('auto_reply_enabled', 'updated_at')


@admin.register(ReplyExample)
class ReplyExampleAdmin(admin.ModelAdmin):
    list_display = ('incoming_preview', 'reply_preview', 'is_active', 'updated_at')
    search_fields = ('incoming_message', 'bilal_reply', 'notes')
    list_filter = ('is_active',)

    @admin.display(description='Incoming message')
    def incoming_preview(self, obj):
        return obj.incoming_message[:80]

    @admin.display(description='Bilal-style reply')
    def reply_preview(self, obj):
        return obj.bilal_reply[:80]


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'display_name', 'language_hint', 'human_takeover', 'is_blocked', 'last_seen_at')
    search_fields = ('phone_number', 'display_name')
    list_filter = ('human_takeover', 'is_blocked', 'language_hint')


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at', 'raw_payload')
    fields = ('direction', 'sender_type', 'text', 'whatsapp_message_id', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('contact', 'is_active', 'escalated', 'escalation_reason', 'last_message_at')
    search_fields = ('contact__phone_number', 'contact__display_name')
    list_filter = ('is_active', 'escalated')
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'direction', 'sender_type', 'whatsapp_message_id', 'created_at')
    search_fields = ('text', 'whatsapp_message_id', 'conversation__contact__phone_number')
    list_filter = ('direction', 'sender_type')
