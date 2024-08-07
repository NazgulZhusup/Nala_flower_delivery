# flowers/api_views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Product, Order, OrderItem
from django.contrib.auth.models import User
from rest_framework import viewsets  # Импорт viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product
from .serializers import ProductSerializer

# Сериализатор продуктов
class ProductViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Product.objects.all()
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        # Получаем продукт по его ID
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
# API для создания заказа
@api_view(['POST'])
def create_order(request):
    try:
        user_id = request.data.get('user_id')
        product_ids = request.data.get('product_ids', [])
        quantities = request.data.get('quantities', [])
        address = request.data.get('address')

        # Проверка входных данных
        if not address or len(address) < 10:
            return Response({'error': 'Invalid address'}, status=status.HTTP_400_BAD_REQUEST)

        if len(product_ids) != len(quantities):
            return Response({'error': 'Product IDs and quantities do not match'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, pk=user_id)

        # Создание заказа
        order = Order.objects.create(user=user, address=address, status='pending')

        # Логирование создания заказа
        print(f"Creating order for user {user.username} with address {address}")

        for product_id, quantity in zip(product_ids, quantities):
            product = get_object_or_404(Product, id=product_id)
            OrderItem.objects.create(order=order, product=product, quantity=quantity)

        return Response({'message': 'Order created successfully'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        # Логирование ошибки на сервере
        print(f"Error creating order: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)