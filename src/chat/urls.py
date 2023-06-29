from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
        path('',views.Login,name='login'),
        path('register/',views.Register.as_view(),name='register'),
        path("logout/",views.Logout,name="logout"),
        path("chat/",views.chat,name="chat"),
        path('history/', views.IndexViewHistory.as_view(), name='history'),
        path("summarize/",views.summarize,name="summarize"),
        path("top/",views.top,name="top"),
#        path('', views.chat, name='chat'),
#        path('top/', views.TopView.as_view(), name='top'),
]
