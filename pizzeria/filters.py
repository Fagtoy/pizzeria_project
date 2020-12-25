from collections import Counter

import django_filters

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
            pizzas_names = []
            ingredients_name = list(value)
            queryset = queryset.filter(ingredients__name__in=ingredients_name)
            for key, value in Counter(queryset).items():
                if value == len(ingredients_name):
                    pizzas_names.append(key)
            queryset = Pizza.objects.filter(name__in=pizzas_names, in_stock=True)
            return queryset
        else:
            return queryset
