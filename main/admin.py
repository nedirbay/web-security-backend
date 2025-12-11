from django.contrib import admin
from .models import BlogCategory, Blog, Scan, Alert

admin.site.register(BlogCategory)
admin.site.register(Blog)
admin.site.register(Scan)
admin.site.register(Alert)
