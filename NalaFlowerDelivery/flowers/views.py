# flowers/views.py

from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import SignUpForm, OrderForm
from .models import Product, CartItem, Order, OrderItem
from django.shortcuts import get_object_or_404, redirect, render
from .models import CartItem
from .forms import CheckoutForm
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .models import Order, Product
from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer


class OrderCreateView(APIView):
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        product_ids = request.data.get('product_ids')
        quantities = request.data.get('quantities')
        address = request.data.get('address')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "No User matches the given query."}, status=status.HTTP_400_BAD_REQUEST)

        # Создайте заказ
        order = Order.objects.create(user=user, address=address)

        # Добавьте продукты в заказ
        for product_id, quantity in zip(product_ids, quantities):
            product = Product.objects.get(id=product_id)
            order.items.create(product=product, quantity=quantity)

        return Response({"message": "Order created successfully!"}, status=status.HTTP_201_CREATED)

# views.py


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer



def index(request):
    return render(request, 'flowers/index.html')
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()  # Сохраняем пользователя
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)  # Выполняем вход в систему
                return redirect('index')  # Перенаправление на главную страницу
        else:
            print(form.errors)  # Вывод ошибок валидации для отладки
    else:
        form = SignUpForm()
    return render(request, 'flowers/signup.html', {'form': form})  # Путь к шаблону

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'flowers/login.html', {'form': form})

@login_required
def catalog(request):
    products = Product.objects.all()
    return render(request, 'flowers/catalog.html', {'products': products})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('flower/cart')

@login_required
def cart_view(request):
    cart_items = OrderItem.objects.filter(order__user=request.user, order__status='pending')
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        # Process checkout form
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.get(user=request.user, status='pending')
            order.address = form.cleaned_data['address']
            order.postal_code = form.cleaned_data['postal_code']
            order.city = form.cleaned_data['city']
            order.country = form.cleaned_data['country']
            order.status = 'completed'
            order.save()

            messages.success(request, 'Your order has been placed successfully!')
            return redirect('order_history')
    else:
        form = CheckoutForm()

    return render(request, 'flowers/cart.html', {'cart_items': cart_items, 'total_price': total_price, 'form': form})


@login_required
def checkout(request):

    cart_items = CartItem.objects.filter(user=request.user)

    # Рассчитываем общую стоимость и стоимость каждого элемента
    total_price = 0
    for item in cart_items:
        item.total_price = item.product.price * item.quantity  # Добавляем поле total_price
        total_price += item.total_price

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Логика оформления заказа
            # После успешного оформления перенаправляем на страницу успеха
            return redirect('order_success')  # Убедитесь, что это имя соответствует вашему маршруту
    else:
        form = CheckoutForm()

    return render(request, 'flowers/checkout.html', {'form': form, 'cart_items': cart_items, 'total_price': total_price})

@login_required
def order_success(request):
    """
    Display order success page.
    """
    return render(request, 'flowers/order_success.html')
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    for order in orders:
        for item in order.items.all():
            item.total_price = item.product.price * item.quantity  # Вычисляем полную стоимость элемента
    return render(request, 'flowers/order_history.html', {'orders': orders})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    order, created = Order.objects.get_or_create(user=request.user, status='pending')

    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
    if not created:
        order_item.quantity += 1
        order_item.save()

    messages.success(request, f'Added {product.name} to your cart.')
    return redirect('cart')

@login_required
def remove_from_cart(request, product_id):
    """
    Remove a product from the cart.
    """
    product = get_object_or_404(Product, id=product_id)
    order = get_object_or_404(Order, user=request.user, status='pending')

    order_item = OrderItem.objects.filter(order=order, product=product).first()
    if order_item:
        order_item.delete()
        messages.success(request, f'Removed {product.name} from your cart.')
    else:
        messages.error(request, f'{product.name} is not in your cart.')

    return redirect('cart')
@login_required
def update_cart(request, product_id, quantity):
    """
    Update the quantity of a product in the user's cart.
    """
    # Получаем продукт и обновляем количество
    cart_item = get_object_or_404(CartItem, user=request.user, product_id=product_id)

    # Обновляем количество или удаляем товар, если количество 0
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart')
