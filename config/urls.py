from django.contrib import admin
from django.urls import include, path
from assistant.views import data_deletion, privacy_policy, test_chat

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('assistant.urls')),
    path('privacy-policy/', privacy_policy, name='privacy-policy'),
    path('data-deletion/', data_deletion, name='data-deletion'),
    path('test-chat/', test_chat, name='test-chat'),
]
