from django.db import models
from django.db.models import Q, Count


class CategoryManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_sidebar(self):
        return self.get_queryset().annotate(count=Count('pizza'))
