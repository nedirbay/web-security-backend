from django.shortcuts import render
from django_filters.views import FilterView
from .models import Blog, BlogCategory
from .filtrs import BlogFilter
from .serializer import BlogSerializer, BlogCategorySerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view

# get all blogcategories

@api_view(['GET'])
def blogcategory_list(request): 
    blogcategories = BlogCategory.objects.all()
    serializer = BlogCategorySerializer(blogcategories, many=True)
    return Response(serializer.data)

# get all blogs with filter
@api_view(['GET'])
def blog_list(request):
    blogs = Blog.objects.all()
    filter = BlogFilter(request.GET, queryset=blogs)
    serializer = BlogSerializer(filter.qs, many=True)
    return Response(serializer.data)

