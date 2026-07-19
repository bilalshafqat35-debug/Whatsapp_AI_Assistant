from django.contrib import admin
from django.urls import include, path
from assistant.views import test_chat

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('assistant.urls')),
    path('test-chat/', test_chat, name='test-chat'),
]
