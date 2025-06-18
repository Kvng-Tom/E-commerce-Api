from rest_framework import serializers
from .models import *
from products.serializers import ProductSerializer
from .serializers import ShippingAddressSerializer 

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'added_at']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True,)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'status', 'created_at', 'items', 'total_amount']

    def get_total_amount(self, obj):
        total = 0

        for item in obj.items.all():
            total += item.product.price * item.quantity
        return total

class AddToCartSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required =False, default=1, min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True, min_value=1)

class PaymentSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['card', 'cash', 'transfer'])
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    

class OrderHistoryItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name', read_only=True)
    unit_price = serializers.DecimalField(source='product.price', max_digits=12, decimal_places=2, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['name', 'unit_price', 'quantity', 'subtotal']

    def get_subtotal(self, obj):
        return obj.product.price * obj.quantity

class OrderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['method', 'amount']

class OrderHistorySerializer(serializers.ModelSerializer):
    order_number = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source='created_at', format='%Y-%m-%d', read_only=True)
    total = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    items = OrderHistoryItemSerializer(many=True, read_only=True)
    shipping_address = ShippingAddressSerializer( read_only=True)

    class Meta:
        model = Cart
        fields = ['order_number', 'date', 'total', 'payment_method', 'items', 'shipping_address']

    def get_order_number(self, obj):
        return f"ORDER-{obj.id:04d}"

    def get_total(self, obj):
        payment = getattr(obj, 'payment', None)
        return payment.amount if payment else None

    def get_payment_method(self, obj):
        payment = getattr(obj, 'payment', None)
        return payment.method if payment else None

class ProductReviewSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    review = serializers.CharField()

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'rating', 'review', 'created_at']
        read_only_fields = ['user', 'created_at', 'product']

class ShippingAddressSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ShippingAddress
        fields = ['full_name', 'address_line', 'city', 'state', 'postal_code', 'country', 'phone_number']