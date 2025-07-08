from django.urls import path
from . import views
from .views import landing_login,download_orders
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # path('dashboard/', views.dashboard, name='dashboard'),
    path('orders/download/', download_orders, name='download_orders'),
    path('', landing_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('upload/', views.upload_csv, name='upload_csv'),
    # Stores
    path('stores/', views.store_list, name='store_list'),
    path('stores/create/', views.store_create, name='store_create'),
    path('stores/<int:pk>/edit/', views.store_update, name='store_update'),
    path('stores/<int:pk>/delete/', views.store_delete, name='store_delete'),

    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/edit/', views.order_update, name='order_update'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),

    # Addresses
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/create/', views.address_create, name='address_create'),
    path('addresses/<int:pk>/edit/', views.address_update, name='address_update'),
    path('addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),

    # Line Items
    path('lineitems/', views.lineitem_list, name='lineitem_list'),
    path('lineitems/create/', views.lineitem_create, name='lineitem_create'),
    path('lineitems/<int:pk>/edit/', views.lineitem_update, name='lineitem_update'),
    path('lineitems/<int:pk>/delete/', views.lineitem_delete, name='lineitem_delete'),

    # Rules
    path('rules/', views.rule_list, name='rule_list'),
    path('rules/create/', views.rule_create, name='rule_create'),
    path('rules/<int:pk>/edit/', views.rule_update, name='rule_update'),
    path('rules/<int:pk>/delete/', views.rule_delete, name='rule_delete'),

    # Flagged Orders
    path('flaggedorders/', views.flaggedorder_list, name='flaggedorder_list'),
    path('flaggedorders/create/', views.flaggedorder_create, name='flaggedorder_create'),
    path('flaggedorders/<int:pk>/edit/', views.flaggedorder_update, name='flaggedorder_update'),
    path('flaggedorders/<int:pk>/delete/', views.flaggedorder_delete, name='flaggedorder_delete'),
]