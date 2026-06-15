from django.urls import path
from . import views

urlpatterns = [
    path('', views.bulk_message, name='bulk_message'),
    path('log/', views.message_log, name='message_log'),
    path('log-send/', views.log_send, name='log_send'),
]