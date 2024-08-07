from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderItem')
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('completed', 'Completed')])
    order_date = models.DateTimeField(auto_now_add=True)
    address = models.CharField(max_length=255, null=True, blank=True, default='')  # Убедитесь, что default указано
    postal_code = models.CharField(max_length=20, null=True, blank=True, default='') # Убедитесь, что default указано
    city = models.CharField(max_length=100, null=True, blank=True, default='')       # Убедитесь, что default указано
    country = models.CharField(max_length=100, null=True, blank=True, default='')    # Убедитесь, что default указано

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

