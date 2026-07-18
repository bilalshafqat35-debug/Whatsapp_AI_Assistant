from rest_framework import serializers
from .models import AssistantSettings, Contact, Conversation, Message


class AssistantSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantSettings
        fields = '__all__'


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class ConversationSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)
    recent_messages = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = '__all__'

    def get_recent_messages(self, obj):
        return MessageSerializer(obj.messages.order_by('-created_at')[:10], many=True).data
