from django.db import models
from django.conf import settings
from products.models import Product
from django.utils import timezone


# Create your models here.


class Cart(models.Model):

    STATUS_CHOICES = (
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
        ('deleted', 'Deleted')
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='not_paid')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Cart of {self.user.email} "
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Cart {self.cart.id}"


class Payment(models.Model):

    PAYMENT_METHODS = (
        ('card', 'Card'),
        ('cash', 'Cash'),
        ('transfer', 'Transfer'),        
    )

    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name = 'payment')
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits = 10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Payment for Cart {self.cart.id}"
    

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=1)
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.email} for {self.product.name}"
    

class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name='shipping_address')
    full_name = models.CharField(max_length=100)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shipping Address for {self.user.email}"
    
    
