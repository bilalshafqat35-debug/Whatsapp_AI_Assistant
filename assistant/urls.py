from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AssistantSettingsViewSet, ContactViewSet, ConversationViewSet, MessageViewSet, whatsapp_webhook

router = DefaultRouter()
router.register('settings', AssistantSettingsViewSet)
router.register('contacts', ContactViewSet)
router.register('conversations', ConversationViewSet)
router.register('messages', MessageViewSet)

urlpatterns = [
    path('webhooks/whatsapp/', whatsapp_webhook, name='whatsapp-webhook'),
    path('', include(router.urls)),
]
