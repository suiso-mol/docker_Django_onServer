from django.urls import path, include
from . import views

app_name ='users'

urlpatterns = [
    path('', views.TopView.as_view(), name='top'),
    path('login/', views.Login.as_view(), name='login'),
#    path('register',views.Registrer.as_view(), name='register'),
#    path('register_done',views.RegistrerDone.as_view(), name='register_done'),
#    path('logout/', views.Logout.as_view(), name='logout'),
]