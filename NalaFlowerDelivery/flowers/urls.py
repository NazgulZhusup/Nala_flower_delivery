# flowers/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from . import views, api_views
from django.conf import settings

router = DefaultRouter()
router.register(r'products', api_views.ProductViewSet, basename='product')

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('catalog/', views.catalog, name='catalog'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-history/', views.order_history, name='order_history'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('order-success/', views.order_success, name='order_success'),  # Убедитесь, что этот маршрут существует
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),  # Новый маршрут
    path('update_cart/<int:product_id>/<int:quantity>/', views.update_cart, name='update_cart'),  # Маршрут для обновления корзины
    path('api/', include(router.urls)),  # Подключение маршрутов API
    path('api/orders/', api_views.create_order, name='create_order'),  # API для заказов
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)