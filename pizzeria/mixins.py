from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from .models import Category, Pizza, Cart, Customer


class CategoryMixin(SingleObjectMixin):

    def get_context_data(self, **kwargs):
        if isinstance(self.get_object(), Category):
            context = super().get_context_data()
            context['categories'] = Category.objects.get_categories_for_sidebar()
            context['products'] = Pizza.objects.filter(category=self.get_object(), in_stock=True)
            return context
        context = super().get_context_data()
        context['categories'] = Category.objects.get_categories_for_sidebar()
        return context


class CustomerMixin(View):

    def dispatch(self, request, *args, **kwargs):
        self.customer = Customer.objects.get(user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['customer'] = self.customer
        return context


class CartMixin(View):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            customer = Customer.objects.filter(user=request.user).first()
            cart = Cart.objects.filter(customer=customer, in_order=False).first()
            if not cart:
                cart = Cart.objects.create(customer=customer)
        self.cart = cart
        self.cart.save()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['cart'] = self.cart
        return context
