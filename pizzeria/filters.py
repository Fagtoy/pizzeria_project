import django_filters
from django.db.models import Count

from .models import Pizza, Ingredient


class PizzaFilter(django_filters.FilterSet):
    price__gt = django_filters.NumberFilter(field_name='price', lookup_expr='gt')
    price__lt = django_filters.NumberFilter(field_name='price', lookup_expr='lt')
    description_cont = django_filters.CharFilter(field_name='description', lookup_expr='icontains')
    ingredients = django_filters.ModelMultipleChoiceFilter(field_name='ingredients',
                                                           queryset=Ingredient.objects.all(),
                                                           method='filter_ingredients')

    class Meta:
        model = Pizza
        fields = ['price__gt', 'price__lt', 'ingredients', 'category', 'description_cont']

    @staticmethod
    def filter_ingredients(queryset, name, value):
        if name and value:
            value_len = len(value)
            return queryset.filter(id__in=[
                pizza['id'] for pizza in queryset.filter(
                    ingredients__in=value
                ).values('id').annotate(count=Count('id')) if pizza['count'] == value_len
            ])
        else:
            return queryset
