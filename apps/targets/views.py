"""Views for target management."""
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.targets.models import Target
from apps.targets.serializers.target_serializers import (
    TargetOwnerAssignSerializer,
    TargetSerializer,
    TargetVerificationSerializer,
)

User = get_user_model()


class TargetListCreateView(generics.ListCreateAPIView):
    serializer_class = TargetSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Target.objects.all()
        return Target.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TargetDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = TargetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Target.objects.all()
        return Target.objects.filter(owner=user)


class TargetToggleActiveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        target = get_object_or_404(Target, pk=pk)
        if not (request.user.is_staff or target.owner_id == request.user.id):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        target.is_active = not target.is_active
        target.save(update_fields=["is_active", "updated_at"])
        return Response({"id": target.id, "is_active": target.is_active}, status=status.HTTP_200_OK)


class TargetVerifyOwnershipView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        target = get_object_or_404(Target, pk=pk)
        if not (request.user.is_staff or target.owner_id == request.user.id):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TargetVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["token"] != target.verification_token:
            return Response({"detail": "Invalid verification token."}, status=status.HTTP_400_BAD_REQUEST)

        target.verification_status = Target.VerificationStatus.VERIFIED
        target.verified_at = timezone.now()
        target.save(update_fields=["verification_status", "verified_at", "updated_at"])
        return Response(TargetSerializer(target).data, status=status.HTTP_200_OK)


class TargetAssignOwnerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff:
            return Response({"detail": "You do not have permission."}, status=status.HTTP_403_FORBIDDEN)

        target = get_object_or_404(Target, pk=pk)
        serializer = TargetOwnerAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_owner = get_object_or_404(User, pk=serializer.validated_data["user_id"])
        target.owner = new_owner
        target.save(update_fields=["owner", "updated_at"])
        return Response(TargetSerializer(target).data, status=status.HTTP_200_OK)
