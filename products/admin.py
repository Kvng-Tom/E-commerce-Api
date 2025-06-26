from django.contrib import admin
from .models import Product, Category
from cart.models import Cart, CartItem, Payment, ProductReview, ShippingAddress

# Register your models here.
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Payment)
admin.site.register(ProductReview)
admin.site.register(ShippingAddress)
