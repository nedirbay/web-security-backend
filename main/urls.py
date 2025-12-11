from django.urls import path
from .views import blogcategory_list, blog_list, adminLogin
from .views import OWASPScanView, blog_detail
urlpatterns = [
    path('blogcategory/', blogcategory_list, name='blogcategory_list'),
    path('blog/', blog_list, name='blog_list'),
    path('blog/<int:pk>/', blog_detail, name='blog_detail'),
    path('adminLogin/', adminLogin, name='adminLogin'),
    path('scan/', OWASPScanView.as_view(), name='owasp-scan'),
]
