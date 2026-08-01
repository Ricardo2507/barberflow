# apps/core/urls.py
from django.urls import path
from . import views # Importa as views do próprio app core

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"), # A view 'home' do app core
    path("assistente/", views.assistente, name="assistente"), # Adicione esta linha
    path(
        "api/ai-assistant/",
        views.ai_assistant_api, # A view 'ai_assistant_api' do app core
        name="ai_assistant_api",
    ),
]