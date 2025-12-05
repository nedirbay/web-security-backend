from django_filters import FilterSet
from .models import Blog

class BlogFilter(FilterSet):
    class Meta:
        model = Blog
        fields = ['category']

