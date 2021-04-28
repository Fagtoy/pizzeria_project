from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.utils import IntegrityError
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import DetailView, CreateView
from django.views.generic.base import View

from .filters import PizzaFilter
from .forms import OrderForm, CreateUserForm
from .mixins import CategoryMixin, CartMixin, CustomerMixin
from .models import *
from .utils import calculate_cart_total, calculate_cart_product_total


@transaction.atomic()
def registration(request):
    if request.user.is_authenticated:
        return redirect('base')

    else:
        form = CreateUserForm()

        if request.method == 'POST':
            form = CreateUserForm(request.POST or None)

            if form.is_valid():
                try:
                    user = form.save()
                    Token.objects.create(user=user)
                    phone_number = form.cleaned_data['phone_number']
                    address = form.cleaned_data['address']
                    customer = Customer.objects.create(user=user, phone_number=phone_number, address=address)
                    customer.save()
                    username = form.cleaned_data['username']
                    messages.success(request, f'Account was created for {username}')
                    return redirect('login')
                except IntegrityError:
                    context = {'form': form}
                    messages.info(request, f'Phone already exist')
                    return render(request, 'registration.html', context)
        context = {'form': form}
        return render(request, 'registration.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('base')

    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None and Token.objects.filter(user=user).exists():
                login(request, user)
                return redirect('base')
            else:
                messages.info(request, 'Username or password is incorrect')

        context = {}
        return render(request, 'login.html', context)


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')


class BaseView(LoginRequiredMixin, CartMixin, View):
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        customer = Customer.objects.get(user=request.user)
        f = PizzaFilter(request.GET, queryset=Pizza.objects.filter(in_stock=True))
        context = {
            'categories': Category.objects.get_categories_for_sidebar(),
            'cart': self.cart,
            'customer': customer,
            'filter': f
        }
        return render(request, 'base.html', context)


class ProductDetailView(CustomerMixin, CartMixin, CategoryMixin, DetailView):
    model = Pizza
    context_object_name = 'product'
    template_name = 'product_detail.html'

    def get_context_data(self, **kwargs):
        ingredients = Ingredient.objects.filter(related_pizza__slug=self.kwargs.get('slug'))
        context = super().get_context_data(**kwargs)
        context['ingredients'] = ingredients
        return context


class ProfileDetailView(CustomerMixin, LoginRequiredMixin, CartMixin, CategoryMixin, DetailView):
    login_url = 'login'
    model = Customer
    context_object_name = 'customer'
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        orders = Order.objects.filter(customer=self.customer).order_by('-id')
        context = super().get_context_data(**kwargs)
        context['orders'] = orders
        return context


class CategoryDetailView(CustomerMixin, CartMixin, CategoryMixin, DetailView):
    model = Category
    template_name = 'category_list.html'


class OrderDetailView(CustomerMixin, CartMixin, CategoryMixin, DetailView):
    model = Order
    template_name = 'order_view.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        order = Order.objects.get(pk=self.kwargs.get('pk'))
        context = super().get_context_data(**kwargs)
        context['current_cart'] = order.cart
        return context


class CartView(CustomerMixin, LoginRequiredMixin, CartMixin, View):
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories_for_sidebar()
        context = {
            'cart': self.cart,
            'categories': categories,
            'products': self.cart.products.all(),
            'customer': self.customer
        }
        return render(request, 'cart.html', context)


class AddProductToCartView(LoginRequiredMixin, CartMixin, View):
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Pizza.objects.get(slug=product_slug)
        cart_product, created = CartProduct.objects.select_related('product').get_or_create(
            customer=self.cart.customer, cart=self.cart, product=product
        )
        if created:
            cart_product.final_price = product.price
            cart_product.save()
            self.cart.products.add(cart_product)
        else:
            calculate_cart_product_total(cart_product, cart_product.qty + 1)
        calculate_cart_total(self.cart)
        return redirect('cart')


class DeleteFromCartView(LoginRequiredMixin, CartMixin, View):
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Pizza.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            customer=self.cart.customer, cart=self.cart, product=product
        )
        self.cart.products.remove(cart_product)
        cart_product.delete()
        calculate_cart_total(self.cart)
        return redirect('cart')


class ChangeQtyView(LoginRequiredMixin, CartMixin, View):
    login_url = 'login'

    def post(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Pizza.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.select_related('product').get(
            customer=self.cart.customer, cart=self.cart, product=product
        )
        qty = int(request.POST.get('qty'))
        calculate_cart_product_total(cart_product, qty)
        calculate_cart_total(self.cart)
        return redirect('cart')


class FinishOrderView(CustomerMixin, LoginRequiredMixin, CartMixin, CreateView):
    form_class = OrderForm
    login_url = 'login'
    template_name = 'checkout.html'

    def get_initial(self):
        customer = self.customer
        return dict(first_name=customer.user.first_name, last_name=customer.user.last_name, phone=customer.phone_number,
                    address=customer.address, order_date_time=timezone.now() + timedelta(hours=1, minutes=5))

    def get_success_url(self):
        return reverse('base')

    def form_valid(self, form):
        order = form.save(commit=False)
        order.customer = self.customer
        order.save()
        self.cart.in_order = True
        self.cart.save()
        order.cart = self.cart
        order.save()
        self.customer.orders.add(order)
        return super().form_valid(form)
