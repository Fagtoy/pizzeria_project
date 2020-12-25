from rest_framework import generics
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .serializers import CategorySerializer, PizzaSerializer, OrderSerializer, CartSerializer, CustomerSerializer
from ..models import *


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'slug']
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method in ['GET']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class PizzaViewSet(viewsets.ModelViewSet):
    serializer_class = PizzaSerializer
    queryset = Pizza.objects.all()
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['price', 'name', 'category__slug']
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method in ['GET']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        name = request.data['name']
        ingredients = Ingredient.objects.filter(name__in=request.data['ingredients'].split(', '))
        slug = request.data['slug']
        price = request.data['price']
        category = Category.objects.get(name__in=request.data['category'].split(r'[A-Z][a-z]+'))
        image = request.data['image']
        description = request.data['description']
        in_stock = request.data['in_stock']
        new_pizza = Pizza.objects.create(name=name, slug=slug, image=image, category=category,
                                         price=price, description=description, in_stock=in_stock)
        new_pizza.ingredients.set(ingredients)
        new_pizza.save()
        return Response({'response': 'Creation success'})


class OrderAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method in ['GET']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    def delete(self, request, *args, **kwargs):
        user = request.user
        customer = Customer.objects.get(user=user)
        order = self.get_object()
        if order.customer != customer:
            return Response({'response': 'You aren\'t from the club buddy!'})
        return self.destroy(request, *args, **kwargs)


class CartAPIView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'


class CustomerAPIView(generics.RetrieveAPIView):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
