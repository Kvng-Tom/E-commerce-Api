from rest_framework import serializers
from .models import *




class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):

    # This field allows us to set category by ID when creating or updating a product
    category_id = serializers.PrimaryKeyRelatedField(
        
        queryset=Category.objects.all(), source='category', write_only=True, required=False)


    class Meta:
        model = Product
        fields = '__all__'