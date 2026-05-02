"""Маршруты публичной части приложения shop."""
from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.catalog, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/add/', views.product_create, name='product_add'),
    path('product/<int:pk>/edit/', views.product_update, name='product_edit'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('category/<int:pk>/', views.category_products, name='category_products'),
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/add/', views.promotion_create, name='promotion_add'),
    path('promotions/<int:pk>/edit/', views.promotion_update, name='promotion_edit'),
    path('promotions/<int:pk>/delete/', views.promotion_delete, name='promotion_delete'),
    path('lab2/', views.lab2_report, name='lab2_report'),
    path('lab2/mutation-demo/', views.orm_mutation_demo, name='orm_mutation_demo'),
]
