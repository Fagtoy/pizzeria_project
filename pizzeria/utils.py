import sys
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.safestring import mark_safe


def get_image(obj, width, height):
    return mark_safe(f'<img src={obj.image.url} width="{width}" height="{height}"')


def change_image_resolution(image, min_resolution, max_resolution, max_image_size, new_image_width, new_image_height):
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


def calculate_cart_product_total(cart_product, qty):
    cart_product.qty = qty
    cart_product.final_price = cart_product.product.price * qty
    cart_product.save()


def calculate_cart_total(cart):
    final_price = 0
    total_products = 0
    products_data = list(cart.products.all().values_list('final_price', flat=True))
    for product_final_price in products_data:
        final_price += product_final_price
        total_products += 1
    cart.total_products = total_products
    cart.final_price = final_price
    cart.save()
