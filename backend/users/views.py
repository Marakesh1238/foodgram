from rest_framework import generics, permissions, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from django.shortcuts import get_object_or_404

from recipes.models import Subscription
from .models import CustomUser
from api.serializers import (AvatarUpdateSerializer,
                             CustomUserDetailSerializer,
                             CustomUserSerializer, SubscriptionSerializer)


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


class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(CustomUser, pk=pk)
        if user == author:
            return Response({"detail": "Cannot subscribe to yourself."}, status=status.HTTP_400_BAD_REQUEST)
        if Subscription.objects.filter(user=user, author=author).exists():
            return Response({"detail": "Already subscribed."}, status=status.HTTP_400_BAD_REQUEST)
        Subscription.objects.create(user=user, author=author)
        return Response(CustomUserSerializer(author, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='subscribe')
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(CustomUser, pk=pk)
        subscription = get_object_or_404(Subscription, user=user, author=author)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)