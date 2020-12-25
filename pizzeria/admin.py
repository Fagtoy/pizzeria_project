from django.contrib import admin

from .models import *


class PizzaInline(admin.TabularInline):
    model = Pizza
    extra = 0
    fields = ['name', 'slug', 'ingredients', 'price']
    readonly_fields = fields

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CartProductInline(admin.TabularInline):
    model = CartProduct
    extra = 0
    readonly_fields = ['customer', 'product', 'qty', 'final_price']

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class OrderInline(admin.TabularInline):
    model = Order
    extra = 0
    readonly_fields = [
        'customer', 'first_name', 'last_name', 'phone', 'address',
        'status', 'delivery', 'comment', 'order_date_time', 'created_at'
    ]

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Pizza)
class PizzaAdmin(admin.ModelAdmin):
    readonly_fields = ['get_image']
    filter_horizontal = ['ingredients']
    list_filter = ['category', 'in_stock', 'ingredients']
    search_fields = ['name', 'ingredients__name']


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_image']
    readonly_fields = ['get_image']
    search_fields = ['name', 'related_pizza__name']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['customer', 'id']
    list_display_links = ['customer']
    inlines = [CartProductInline, OrderInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [PizzaInline]
    search_fields = ['pizza__name']


admin.site.register(Customer)
admin.site.register(CartProduct)
admin.site.register(Order)
