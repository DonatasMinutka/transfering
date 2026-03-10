from django.urls import path
from . import views

urlpatterns = [
    path('devices/<int:pk>/', views.KakDeviceView.as_view(), name='kak_device_view'),
    path('devices/add/', views.KakDeviceEditView.as_view(), name='kak_device_add'),
    path('devices/<int:pk>/edit/', views.KakDeviceEditView.as_view(), name='kak_device_edit'),
    path('devices/<int:pk>/', views.DefaultDeviceView.as_view(), name='default_device_view'),
    path('add_site/', views.KakSiteCreateView.as_view(), name='add_site'), 
    path('site/<int:pk>/edit/', views.KakSiteCreateView.as_view(), name='edit_site'), 
    path('add_tenant/', views.KakTenantCreateView.as_view(), name='add_tenant'), 
    path('tenant/<int:pk>/edit/', views.KakTenantCreateView.as_view(), name='edit_tenant'),     
]