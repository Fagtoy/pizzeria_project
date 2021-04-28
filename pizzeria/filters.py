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
            pizza_ids = list(queryset.filter(ingredients__in=value).values_list('id', flat=True))
            filtered_pizza_ids = []
            for k, v in Counter(pizza_ids).items():
                if v == len(value):
                    filtered_pizza_ids.append(k)
            return queryset.filter(id__in=filtered_pizza_ids)
        else:
            return queryset
