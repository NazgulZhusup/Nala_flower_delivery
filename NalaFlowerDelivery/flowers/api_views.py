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
from .serializers import OrderSerializer, ProductSerializer

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



@api_view(['POST'])
def create_order(request):
    try:
        user_id = request.data.get('user_id')
        product_ids = request.data.get('product_ids', [])
        quantities = request.data.get('quantities', [])
        address = request.data.get('address')

        if not (user_id and product_ids and quantities and address):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user_id=user_id, address=address)
        for product_id, quantity in zip(product_ids, quantities):
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(order=order, product=product, quantity=quantity)

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
