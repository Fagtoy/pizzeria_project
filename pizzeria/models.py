import sys
from io import BytesIO

from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.safestring import mark_safe
from rest_framework.authtoken.models import Token


def get_image(obj, width, height):
    return mark_safe(f'<img src={obj.image.url} width="{width}" height="{height}"')


def change_image_resolution(**kwargs):
    image = kwargs.get('image')
    min_resolution = kwargs.get('min_resolution')
    max_resolution = kwargs.get('max_resolution')
    max_image_size = kwargs.get('max_image_size')
    new_image_width = kwargs.get('new_image_width')
    new_image_height = kwargs.get('new_image_height')

    img = Image.open(image)
    min_height, min_width = min_resolution
    max_height, max_width = max_resolution
    if image.size > max_image_size:
        raise Exception(f'Uploaded images\'s size could not be bigger than {max_image_size}')
    if img.height < min_height or img.width < min_width or img.height > max_height or img.width > max_width:
        new_img = img.convert('RGB')
        resized_new_image = new_img.resize((new_image_width, new_image_height), Image.ANTIALIAS)
        file_stream = BytesIO()
        resized_new_image.save(file_stream, 'JPEG', quality=90)
        file_stream.seek(0)
        name = image.name
        image = InMemoryUploadedFile(
            file_stream, 'ImageField', name, 'jpeg/image', sys.getsizeof(file_stream), None
        )
    return image


class Pizza(models.Model):
    min_resolution = (600, 400)
    max_resolution = (650, 450)
    max_image_size = 3145728
    new_image_width = 625
    new_image_height = 425

    name = models.CharField(max_length=255, verbose_name='Name', unique=True)
    ingredients = models.ManyToManyField('Ingredient', related_name='related_pizza', verbose_name='Ingredients')
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Price')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name='Category')
    image = models.ImageField(verbose_name='Image')
    description = models.TextField(verbose_name='Description')
    in_stock = models.BooleanField(default=True, verbose_name='In stock')
    slug = models.SlugField(unique=True, verbose_name='Slug')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        self.image = change_image_resolution(image=self.image,
                                             min_resolution=self.min_resolution,
                                             max_resolution=self.max_resolution,
                                             max_image_size=self.max_image_size,
                                             new_image_width=self.new_image_width,
                                             new_image_height=self.new_image_height)
        super().save(*args, **kwargs)

    def get_image(self):
        image = get_image(self, self.new_image_width, self.new_image_height)
        return image


class Ingredient(models.Model):
    min_resolution = (100, 100)
    max_resolution = (100, 100)
    max_image_size = 3145728
    new_image_width = 100
    new_image_height = 100

    image = models.ImageField(verbose_name='Image', null=True)
    name = models.CharField(max_length=50, verbose_name='Name')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.image = change_image_resolution(image=self.image,
                                             min_resolution=self.min_resolution,
                                             max_resolution=self.max_resolution,
                                             max_image_size=self.max_image_size,
                                             new_image_width=self.new_image_width,
                                             new_image_height=self.new_image_height)
        super().save(*args, **kwargs)

    def get_image(self):
        image = get_image(self, self.new_image_width, self.new_image_height)
        return image


class CategoryManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_sidebar(self):
        qs = list(self.get_queryset().annotate(models.Count('pizza')))
        context = [dict(name=category.name, url=category.get_absolute_url,
                        count=getattr(category, 'pizza__count')) for category in qs]
        return context


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Name', unique=True)
    slug = models.SlugField(unique=True, verbose_name='Slug')
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_list', kwargs={'slug': self.slug})


class CartProduct(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, verbose_name='Owner')
    cart = models.ForeignKey('Cart', related_name='related_products', null=True,
                             on_delete=models.CASCADE, verbose_name='Cart')
    product = models.ForeignKey(Pizza, on_delete=models.CASCADE, null=True, verbose_name='Pizza')
    qty = models.PositiveSmallIntegerField(default=1, verbose_name='Qty')
    final_price = models.DecimalField(max_digits=9, decimal_places=2, default=0, verbose_name='Final price')

    def __str__(self):
        return f'{self.customer}\'s cart product'


class Cart(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, verbose_name='Owner', null=True)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart', verbose_name='Products')
    total_products = models.PositiveSmallIntegerField(default=0, verbose_name='Quantity of products')
    final_price = models.DecimalField(max_digits=9, decimal_places=2, default=0, verbose_name='Final price')
    in_order = models.BooleanField(default=False)
    for_anon_user = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.customer}\'s cart'

    def get_total(self, *args, **kwargs):
        final_price = 0
        total_products = 0
        for product in self.products.all():
            product.final_price = product.product.price * product.qty
            product.save()
            final_price += product.final_price
            total_products += product.qty
        self.total_products = total_products
        self.final_price = final_price
        return self.save()


class Customer(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, verbose_name='Customer')
    phone_number = models.CharField(max_length=20, verbose_name='Phone number', unique=True)
    address = models.CharField(max_length=150, verbose_name='Address')
    orders = models.ManyToManyField('Order', related_name='related_customer', verbose_name='Orders', blank=True)

    def __str__(self):
        return str(self.user)

    def get_absolute_url(self):
        return reverse('profile', kwargs={'pk': self.pk})


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in progress'
    STATUS_READY = 'ready'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = (
        (STATUS_NEW, 'New order'),
        (STATUS_IN_PROGRESS, 'Order\'s in progress'),
        (STATUS_READY, 'Order\'s ready'),
        (STATUS_COMPLETED, 'Order\'s completed')
    )

    DELIVERY_ON = 'delivery'
    DELIVERY_OFF = 'pickup'

    DELIVERY_CHOICES = (
        (DELIVERY_ON, 'I need delivery'),
        (DELIVERY_OFF, 'I don\'t need delivery (pickup)')
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='related_orders',
                                 verbose_name='Buyer')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, blank=True,
                             verbose_name='Cart', related_name='related_order')
    first_name = models.CharField(max_length=255, verbose_name='First name')
    last_name = models.CharField(max_length=255, verbose_name='Last name')
    phone = models.CharField(max_length=255, verbose_name='Phone')
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name='Address')
    status = models.CharField(max_length=100, verbose_name='Order\'s status',
                              choices=STATUS_CHOICES, default=STATUS_NEW)
    delivery = models.CharField(max_length=100, verbose_name='Delivery',
                                choices=DELIVERY_CHOICES, default=DELIVERY_OFF)
    comment = models.TextField(null=True, blank=True, verbose_name='Comment to the order')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Order\'s created at')
    order_date_time = models.DateTimeField(auto_now_add=False, verbose_name='Order\'s delivery date and time')

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        return reverse('order_view', kwargs={'pk': self.pk})


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
