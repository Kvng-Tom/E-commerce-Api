from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import path, include

router = DefaultRouter()
router.register(r'products', ProductViewSet , basename='product')



urlpatterns = [
        path('products/<int:pk>/', ProductDetailView.as_view(), ),
        path('categories/', CategoryListCreateView.as_view()),
        path('categories/<int:pk>/', CategoryDetailView.as_view()),
        path('categories/<int:pk>/delete/', CategoryDestroyView.as_view()),
        path('categories/<int:pk>/products/', CategoryProductsView.as_view()),


]

urlpatterns += router.urls
# This code sets up the URL routing for the products app in a my e-commerce project.