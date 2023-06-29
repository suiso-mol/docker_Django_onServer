from django.urls import path
from django.contrib.auth.views import LoginView
from . import views
app_name = 'vuln'
urlpatterns = [
    path('', views.IndexViewServer.as_view(), name='server_list'),
    path('search/', views.search_free, name='search_free'),
    path('<slug:sv_id>/', views.IndexViewContent.as_view(), name='content_list'),
    path('search_n/<slug:sv_pkg>/', views.search_nvd, name='nvd_list'),
    path('search_j/<slug:sv_pkg>/', views.search_myjvn, name='myjvn_list'),
    path('db_index/list/', views.DbIndex.as_view(), name='db_list'),
    path('db_index/import/', views.DbImport.as_view(), name='db_import'),
    path('db_index/export/', views.db_export, name='db_export'),
    path('db_index/extra/', views.DbIndex.as_view(), name='db_qdetail'),
]
