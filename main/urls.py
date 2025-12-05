from django.urls import path
from .views import blogcategory_list, blog_list

urlpatterns = [
    path('blogcategory/', blogcategory_list, name='blogcategory_list'),
    path('blog/', blog_list, name='blog_list'),
]
