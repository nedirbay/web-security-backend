"""Admin panel API views."""
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import AuditLog, BlogPost, DocumentationPage, Role, SystemSetting
from apps.core.security import AdminIPWhitelistPermission
from apps.core.serializers import (
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AssignTargetSerializer,
    AuditLogSerializer,
    BlogPostSerializer,
    DocumentationPageSerializer,
    RoleSerializer,
    SystemSettingSerializer,
)
from apps.scans.models import Scan, Vulnerability
from apps.targets.models import Target

User = get_user_model()


class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser, AdminIPWhitelistPermission]

    def get(self, request):
        data = {
            "total_scans": Scan.objects.count(),
            "active_targets": Target.objects.filter(is_active=True).count(),
            "critical_vulnerabilities": Vulnerability.objects.filter(severity="High", is_false_positive=False).count(),
            "system_health": {
                "failed_scans": Scan.objects.filter(status=Scan.Status.FAILED).count(),
                "queued_scans": Scan.objects.filter(status=Scan.Status.QUEUED).count(),
                "users_total": User.objects.count(),
            },
        }
        return Response(data, status=status.HTTP_200_OK)


class AdminUserListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser, AdminIPWhitelistPermission]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all().select_related("role")
    pagination_class = None


class AdminUserManageView(APIView):
    permission_classes = [permissions.IsAdminUser, AdminIPWhitelistPermission]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = AdminUserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        changed = {}
        role_id = serializer.validated_data.get("role_id")
        if role_id is not None:
            role = get_object_or_404(Role, pk=role_id)
            user.role = role
            changed["role"] = role.name

        if "is_active" in serializer.validated_data:
            user.is_active = serializer.validated_data["is_active"]
            changed["is_active"] = user.is_active

        if changed:
            user.save(update_fields=[*(["role"] if "role" in changed else []), *(["is_active"] if "is_active" in changed else []), "updated_at"])
            AuditLog.objects.create(
                actor=request.user,
                action="admin_user_update",
                entity_type="user",
                entity_id=user.id,
                metadata=changed,
            )

        return Response(AdminUserSerializer(user).data, status=status.HTTP_200_OK)


class AdminAssignTargetView(APIView):
    permission_classes = [permissions.IsAdminUser, AdminIPWhitelistPermission]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = AssignTargetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target = get_object_or_404(Target, pk=serializer.validated_data["target_id"])
        target.owner = user
        target.save(update_fields=["owner", "updated_at"])

        AuditLog.objects.create(
            actor=request.user,
            action="admin_assign_target",
            entity_type="target",
            entity_id=target.id,
            metadata={"assigned_to": user.id},
        )
        return Response({"target_id": target.id, "owner_id": user.id}, status=status.HTTP_200_OK)


class RoleListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser, AdminIPWhitelistPermission]
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    pagination_class = None


class SystemSettingListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminUser, AdminIPWhitelistPermission]
    serializer_class = SystemSettingSerializer
    queryset = SystemSetting.objects.all()
    pagination_class = None

    def perform_create(self, serializer):
        setting = serializer.save(updated_by=self.request.user)
        AuditLog.objects.create(
            actor=self.request.user,
            action="system_setting_create",
            entity_type="system_setting",
            entity_id=setting.id,
            metadata={"key": setting.key},
        )


class SystemSettingDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAdminUser, AdminIPWhitelistPermission]
    serializer_class = SystemSettingSerializer
    queryset = SystemSetting.objects.all()

    def perform_update(self, serializer):
        setting = serializer.save(updated_by=self.request.user)
        AuditLog.objects.create(
            actor=self.request.user,
            action="system_setting_update",
            entity_type="system_setting",
            entity_id=setting.id,
            metadata={"key": setting.key},
        )


class AuditLogListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser, AdminIPWhitelistPermission]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all().select_related("actor")
    pagination_class = None


class BlogPostListCreateView(generics.ListCreateAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = BlogPost.objects.all().select_related("author")
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            qs = qs.filter(status=BlogPost.Status.PUBLISHED)

        search = self.request.query_params.get("search")
        status_q = self.request.query_params.get("status")
        tag = self.request.query_params.get("tag")
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search) | Q(tags__icontains=search))
        if status_q:
            qs = qs.filter(status=status_q)
        if tag:
            qs = qs.filter(tags__icontains=tag)
        return qs

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admin users can create blog posts.")
        serializer.save(author=self.request.user)


class BlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = BlogPost.objects.all().select_related("author")
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            qs = qs.filter(status=BlogPost.Status.PUBLISHED)
        return qs

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admin users can update blog posts.")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admin users can delete blog posts.")
        instance.delete()


class DocumentationPageListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentationPageSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = DocumentationPage.objects.all()
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            qs = qs.filter(is_published=True)

        search = self.request.query_params.get("search")
        category = self.request.query_params.get("category")
        published = self.request.query_params.get("is_published")
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))
        if category:
            qs = qs.filter(category__icontains=category)
        if published in {"true", "false"}:
            qs = qs.filter(is_published=(published == "true"))
        return qs

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admin users can create documentation pages.")
        serializer.save()


class DocumentationPageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentationPageSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = DocumentationPage.objects.all()
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            qs = qs.filter(is_published=True)
        return qs

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admin users can update documentation pages.")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admin users can delete documentation pages.")
        instance.delete()
