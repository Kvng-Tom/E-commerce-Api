from django.urls import path
from .views import *


urlpatterns =  [
    path('', ViewCartView.as_view()),
    path('add/<int:product_id>/', AddToCartView.as_view()),
    path('item/<int:item_id>/update/', UpdateCartItemView.as_view()),
    path('remove-product-by/<int:product_id>/', RemoveCartItemView.as_view()),
    path('clear/', ClearCartView.as_view()),
    path('checkout/', CheckoutView.as_view()),
    path('orders/', OrderHistoryView.as_view()),
    path('<int:product_id>/review/', ProductReviewView.as_view()),
    path('<int:product_id>/reviews/', ProductReviewListView.as_view()),
    path('shipping-address/', ShippingAddressView.as_view()),
]