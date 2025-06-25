from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import *
from products.models import Product
from .serializers import *
from drf_yasg.utils import swagger_auto_schema

class AddToCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=AddToCartSerializer)
    def post(self, request, product_id):
        user = request.user
        quantity = request.data.get('quantity')
        if quantity is None:
            quantity = 1
        else:
            try:
                quantity = int(quantity)
            except:
                return Response({'error': 'Quantity must be a number.'}, status=400)

        cart, created = Cart.objects.get_or_create(user=user, status='not_paid')

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=404)

        # Check if enough stock is available
        if product.available_quantity < quantity:
            return Response({
                                'error': 'Not enough stock available,',
                                'availaible_quantity' : product.available_quantity,
                                'product_name' : product.name
                         }, status=400)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            # Calculate how many more are being added
            diff = quantity
            cart_item.quantity += quantity
        else:
            diff = quantity
            cart_item.quantity = quantity

        # Check again for stock if updating
        if product.available_quantity < diff:
            return Response({'error': 'Not enough stock available.'}, status=400)

        cart_item.save()
        product.available_quantity -= diff
        product.save()

        return Response({'message': f'Added {quantity} of {product.name} to cart.'}, status=200)

class ViewCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user, status='not_paid').first()
        if not cart:
            return Response({'message': 'Cart is empty.'})
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class UpdateCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=UpdateCartItemSerializer)
    def put(self, request, item_id):
        user = request.user

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=user, cart__status='not_paid')
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=404)

        quantity = request.data.get('quantity')
        if not quantity:
            return Response({'error': 'Quantity is required.'}, status=400)
        try:
            quantity = int(quantity)
            if quantity < 1:
                return Response({'error': 'Quantity must be at least 1.'}, status=400)
        except:
            return Response({'error': 'Quantity must be a number.'}, status=400)

        # Calculate the difference to update product stock
        old_quantity = cart_item.quantity
        diff = quantity - old_quantity

        # Check if enough stock is available for increase
        if diff > 0 and cart_item.product.available_quantity < diff:
            return Response({'error': 'Not enough stock available.'}, status=400)

        # Update product stock
        cart_item.product.available_quantity -= diff
        cart_item.product.save()

        cart_item.quantity = quantity
        cart_item.save()

        return Response({'message': 'Cart item updated successfully.'})

class RemoveCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    
    def delete(self, request, product_id):
        user = request.user

        cart = Cart.objects.filter(user=user, status='not_paid').first()
        if not cart:
            return Response({'error': 'No active cart.'}, status=404)
        try:
            cart_item = CartItem.objects.get(cart=cart, product__id=product_id)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=404)

        # Restore product stock
        cart_item.product.available_quantity += cart_item.quantity
        cart_item.product.save()
        cart_item.delete()
        return Response({'message': 'Cart item removed successfully.'})
    
class ClearCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user, status='not_paid').first()
        if not cart:
            return Response({'message': 'Cart is already empty.'})

        # Restore stock for all items
        for item in cart.items.all():                                                                                                                               # type: ignore
            item.product.available_quantity += item.quantity
            item.product.save()

        
        cart.items.all().delete()                                                           # type: ignore  

        return Response({'message': 'Cart cleared successfully.'})
    
class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=PaymentSerializer)
    def post(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user, status='not_paid').first()

        if not cart or cart.items.count() == 0:                                                                                                                                      # type: ignore
            return Response({'error': 'Cart is empty.'}, status=400)

        serializer = PaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        method = serializer.validated_data['method']                                                                                                                            # type: ignore
        amount = serializer.validated_data['amount']                                                                                                                                    # type: ignore

        TAX_RATE = 0.075
        SHIPPING_FEE = 1500

        
        subtotal = 0.0
        for item in cart.items.all():                                                                                                                               # type: ignore                                                                                                                  
            subtotal += float(item.product.price) * item.quantity

        # Calculation of tax and total
        tax = round(subtotal * TAX_RATE, 2)
        total = round(subtotal + tax + SHIPPING_FEE, 2)

        #validation to check if amount is correct
        if amount != total:
            return Response({
                'error': 'Incorrect amount.',
                'expected_amount': total,
                'received_amount': amount
            }, status=400)

        # To change cart status
        cart.status = 'paid'
        cart.save()

        # Save payment info
        Payment.objects.create(cart=cart, method=method, amount=total)

        return Response({
            "message": "Checkout successful.",
            "order_id": cart.id,                                                                                                    # type: ignore
            "subtotal": subtotal,
            "tax": tax,
            "shipping_fee": SHIPPING_FEE,
            "total_amount": total,
            "payment_method": method,
            "status": cart.status,
            "created_at": cart.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "shipping_address": ShippingAddressSerializer(cart.shipping_address).data if cart.shipping_address else None,                                                                                                                                                                                                           # type: ignore
        }, status=200)


class OrderHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        user = request.user

        paid_carts = Cart.objects.filter(user=user, status='paid').order_by('-created_at')
        serializer = OrderHistorySerializer(paid_carts, many=True)

        return Response(serializer.data, status=200)
        
class ProductReviewView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=ProductReviewSerializer)
    def post(self, request, product_id):
        try: 
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=404)

        # This prevent more than one review on a product by a user
        
        if ProductReview.objects.filter(user=request.user, product=product).exists():
            return Response({'error': 'You have already reviewed this product.'}, status=400)
        
        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class ProductReviewListView(APIView):

    def get(self, request, product_id):

        reviews = ProductReview.objects.filter(product__id=product_id)
        serializer = ProductReviewSerializer(reviews, many=True)
        
        return Response(serializer.data, status=200)


class ShippingAddressView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(request_body=ShippingAddressSerializer)
    def post(self, request):
        user = request.user
        
        # Get user's that  they're shopping with)
        cart = Cart.objects.filter(user=user, status='not_paid').first()
        if not cart:
            return Response({'error': 'No active cart found. Add items to cart first.'}, status=400)
        
        # Check if they already have shipping address for this cart
        if hasattr(cart, 'shipping_address'):
            return Response({'error': 'Shipping address already exists. Use PUT to update.'}, status=400)
        
        serializer = ShippingAddressSerializer(data=request.data)

        if serializer.is_valid():
            # Save with BOTH user and cart (your model needs both!)
            serializer.save(user=user, cart=cart)
            return Response({
                'message': 'Shipping address saved successfully!',
                'data': serializer.data
            }, status=201)
        return Response(serializer.errors, status=400)
    
    def get(self, request):

        user = request.user
        # Get shipping address for current active cart
        cart = Cart.objects.filter(user=user, status='not_paid').first()
        
        if not cart or not hasattr(cart, 'shipping_address'):
            return Response({'message': 'No shipping address found.'}, status=404)
            
        serializer = ShippingAddressSerializer(cart.shipping_address)                                                                                                                                                                           # type: ignore
        return Response(serializer.data, status=200)

class OrderConfirmationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        user = request.user

        try:
            cart = Cart.objects.get(id=order_id, user=user, status='paid')
        except Cart.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=404)

        subtotal = sum(float(item.product.price) * item.quantity for item in cart.items.all())                                                                                                                                                                                                              # type: ignore
        tax = round(subtotal * 0.075, 2)
        shipping_fee = 1500
        total = round(subtotal + tax + shipping_fee, 2)

        data = {
            'order_id': cart.id,                                                                                                                                                        # type: ignore
            'order_date': cart.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items': [
                {
                    'product_name': item.product.name,
                    'price': float(item.product.price),
                    'quantity': item.quantity,
                    'total': round(float(item.product.price) * item.quantity, 2)
                } for item in cart.items.all()                                                                                                                                                                                              # type: ignore
            ],
            'summary': {
                'subtotal': subtotal,
                'tax': tax,
                'shipping_fee': shipping_fee,
                'total': total
            },
            'payment_method': cart.payment.method if hasattr(cart, 'payment') else 'Unknown',                                                                                                                               # type: ignore
            'shipping_address': ShippingAddressSerializer(cart.shipping_address).data if hasattr(cart, 'shipping_address') else None,                                                                                                                                       # type: ignore
            'tracking_number': f'TRK{cart.id:06d}'                                                                                                                                  # type: ignore
        }

        return Response({'message': 'Order confirmed.', 'data': data}, status=200)