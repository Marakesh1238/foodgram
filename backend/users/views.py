from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import CustomUser
from api.serializers import (AvatarUpdateSerializer,
                             CustomUserDetailSerializer,
                             CustomUserSerializer)
from .paginations import CustomUserPagination


class CustomUserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomUserPagination


class CustomUserDetailView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserDetailSerializer
    lookup_field = 'id'


class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomUserDetailSerializer

    def get_object(self):
        return self.request.user


class AvatarUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AvatarUpdateSerializer

    def get_object(self):
        return self.request.user


class AvatarDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        instance.avatar.delete()
        instance.avatar = None
        instance.save()
