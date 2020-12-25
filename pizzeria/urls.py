from django.urls import path

from .views import BaseView, ProductDetailView, CategoryDetailView, \
    CartView, AddProductToCartView, DeleteFromCartView, ChangeQtyView, FinishOrderView, \
    registration, login_view, logout_view, ProfileDetailView, OrderDetailView

urlpatterns = [
    path('', BaseView.as_view(), name='base'),
    path('pizzas/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('category/<str:slug>/', CategoryDetailView.as_view(), name='category_list'),
    path('cart/', CartView.as_view(), name='cart'),
    path('add-to-cart/<slug:slug>/', AddProductToCartView.as_view(), name='add_to_cart'),
    path('delete-from-cart/<slug:slug>/', DeleteFromCartView.as_view(), name='delete_from_cart'),
    path('change-qty/<slug:slug>/', ChangeQtyView.as_view(), name='change_qty'),
    path('finish-order/', FinishOrderView.as_view(), name='finish_order'),
    path('registration/', registration, name='registration'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile'),
    path('order/<int:pk>/', OrderDetailView.as_view(), name='order_view'),
]
