from django.shortcuts import render
from rest_framework import viewsets
from .models import Product
from .serializers import *  
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response


# Create your views here.

class ProductViewSet(viewsets.ModelViewSet):
    
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def get_queryset(self):

        queryset = self.queryset
        category = self.request.GET.get('category', None)
        
        min_price = self.request.GET.get('min_price', None)
        max_price = self.request.GET.get('max_price', None)

        if category:
            queryset = queryset.filter(category__name=category)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if  max_price:
            queryset = queryset.filter(price__lte=max_price)
        return queryset
    
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'pk'
    

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryDestroyView(generics.DestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryProductsView(APIView):
    def get(self, request, pk):
        products = Product.objects.filter(category_id=pk)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)