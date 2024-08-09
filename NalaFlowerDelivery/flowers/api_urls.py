# flowers/api_urls.py

from django.urls import path
from .views import ProductListAPIView, OrderCreateAPIView

urlpatterns = [
    path('products/', ProductListAPIView.as_view(), name='product_list_api'),
    path('orders/', OrderCreateAPIView.as_view(), name='order_create_api'),
]
