from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import OrderAPIView, CustomerAPIView, CartAPIView, PizzaViewSet, CategoryViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='categories')
router.register('pizzas', PizzaViewSet, basename='pizzas')

urlpatterns = [
    path('', include(router.urls)),
    path('order/<str:id>/', OrderAPIView.as_view()),
    path('customer/<str:id>/', CustomerAPIView.as_view()),
    path('cart/<str:id>/', CartAPIView.as_view())
]
