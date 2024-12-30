from rest_framework import generics, permissions, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers

from recipes.models import Subscription
from .models import CustomUser
from api.serializers import (AvatarUpdateSerializer,
                             CustomUserDetailSerializer,
                             CustomUserSerializer, SubscriptionSerializer)



User = get_user_model()


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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'avatar']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    permission_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response({'detail': 'Cannot subscribe to yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        if user.is_subscribed:
            return Response({'detail': 'Already subscribed.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_subscribed = True
        user.save()
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='subscribe')
    def unsubscribe(self, request, pk=None):
        user = self.get_object()
        if not user.is_subscribed:
            return Response({'detail': 'Not subscribed.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_subscribed = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)