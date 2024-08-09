from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import SignUpForm, CheckoutForm
from .models import Product, Order, OrderItem
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from .serializers import ProductSerializer, OrderSerializer
from django.contrib.auth.models import User


# API Views

class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class OrderCreateAPIView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderCreateView(APIView):
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        product_ids = request.data.get('product_ids')
        quantities = request.data.get('quantities')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "No User matches the given query."}, status=status.HTTP_400_BAD_REQUEST)

        # Создайте заказ
        order = Order.objects.create(user=user)

        # Добавьте продукты в заказ
        for product_id, quantity in zip(product_ids, quantities):
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(order=order, product=product, quantity=quantity)

        return Response({"message": "Order created successfully!"}, status=status.HTTP_201_CREATED)


# Web Views

def index(request):
    return render(request, 'flowers/index.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                return redirect('index')
        else:
            print(form.errors)
    else:
        form = SignUpForm()
    return render(request, 'flowers/signup.html', {'form': form})


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
def create_order(request):
    product_id = request.GET.get('product_id')
    quantity = request.GET.get('quantity')
    price = request.GET.get('price')

    if product_id and quantity and price:
        try:
            quantity = int(quantity)
            price = float(price)
            total_price = quantity * price

            product = get_object_or_404(Product, id=product_id)
            order = Order.objects.create(user=request.user, total_price=total_price)
            OrderItem.objects.create(order=order, product=product, quantity=quantity)

            return redirect('order_success')
        except ValueError:
            return redirect('cart')
    return redirect('cart')


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Попробуйте найти незавершенный заказ пользователя
    order = Order.objects.filter(user=request.user, status='pending').first()

    # Если существует больше одного "pending" заказа, мы должны очистить их
    # Этот код предотвращает наличие нескольких "pending" заказов
    if Order.objects.filter(user=request.user, status='pending').count() > 1:
        # Удаляем все незавершенные заказы, кроме одного
        orders = Order.objects.filter(user=request.user, status='pending')
        for extra_order in orders[1:]:
            extra_order.delete()
        order = orders.first()

    # Если заказа нет, создаем новый
    if not order:
        order = Order.objects.create(user=request.user, status='pending')

    # Проверяем, существует ли уже такой товар в заказе
    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)

    if not created:
        # Если товар уже существует, обновляем его количество
        order_item.quantity += 1
        order_item.save()

    messages.success(request, f'Added {product.name} to your cart.')
    return redirect('cart')


@login_required
def cart_view(request):
    cart_items = OrderItem.objects.filter(order__user=request.user, order__status='pending')
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.get(user=request.user, status='pending')
            order.status = 'completed'
            order.save()

            messages.success(request, 'Your order has been placed successfully!')
            return redirect('order_history')
    else:
        form = CheckoutForm()

    return render(request, 'flowers/cart.html', {'cart_items': cart_items, 'total_price': total_price, 'form': form})


@login_required
def checkout(request):
    cart_items = OrderItem.objects.filter(order__user=request.user, order__status='pending')
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Создаем заказ и сохраняем итоговую сумму
            order = Order.objects.get(user=request.user, status='pending')
            order.total_price = total_price
            order.status = 'completed'
            order.save()

            # После сохранения заказа перенаправляем на страницу оплаты
            return redirect('payment', order_id=order.id)  # Переход на страницу оплаты с передачей ID заказа
    else:
        form = CheckoutForm()

    return render(request, 'flowers/checkout.html', {'form': form, 'cart_items': cart_items, 'total_price': total_price})

@login_required
def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        # Логика оплаты
        pass

    return render(request, 'flowers/payment.html', {'order': order})

@login_required
def payment_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        # Здесь можно интегрировать систему оплаты, например, через PayPal, Stripe и т.д.
        # После успешной оплаты:
        order.status = 'completed'
        order.save()
        return redirect('order_success')

    return render(request, 'flowers/payment.html', {'order': order})


@login_required
def order_success(request):
    return render(request, 'flowers/order_success.html')


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    for order in orders:
        for item in order.items.all():
            item.total_price = item.product.price * item.quantity
    return render(request, 'flowers/order_history.html', {'orders': orders})



@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    order = Order.objects.filter(user=request.user, status='pending').first()

    if order:
        order_item = OrderItem.objects.filter(order=order, product=product).first()
        if order_item:
            order_item.delete()
            messages.success(request, f'Removed {product.name} from your cart.')
        else:
            messages.error(request, f'{product.name} is not in your cart.')
    return redirect('cart')


@login_required
def update_cart(request, product_id, quantity):
    order = Order.objects.filter(user=request.user, status='pending').first()

    if order:
        order_item = OrderItem.objects.filter(order=order, product_id=product_id).first()
        if order_item:
            if quantity > 0:
                order_item.quantity = quantity
                order_item.save()
            else:
                order_item.delete()

    return redirect('cart')
