from django.contrib import admin

from apps.core.models import AuditLog, BlogPost, DocumentationPage, Notification, Role, SystemSetting


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "created_at")


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "updated_by", "updated_at")
    search_fields = ("key",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "entity_type", "entity_id", "actor", "created_at")
    list_filter = ("action", "entity_type")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type", "is_read", "sent_at")
    list_filter = ("type", "is_read")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "status", "published_at", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "slug")


@admin.register(DocumentationPage)
class DocumentationPageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "is_published", "updated_at")
    list_filter = ("category", "is_published")
    search_fields = ("title", "slug")
