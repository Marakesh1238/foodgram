from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST
)

from api.constants import PER_PAGE

from .models import Subscription, User
from .serializers import (
    AvatarSerializer,
    SubscriptionSerializer,
    SubscriptionShowSerializer,
    UserSerializer
)


class FoodgramPagination(PageNumberPagination):
    """Пагинация для проекта"""

    page_size = PER_PAGE
    page_size_query_param = 'limit'


class UserViewSet(UserViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = FoodgramPagination
    lookup_field = 'id'
    filter_backends = (SearchFilter,)
    search_fields = ('username',)
    http_method_names = ('get', 'post', 'put', 'delete')

    @action(
        detail=False,
        methods=('patch',),
        url_path='me',
        url_name='me',
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):

        serializer = UserSerializer(
            request.user, data=request.data,
            partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_200_OK)

    @me.mapping.get
    def me_get(self, request):
        serializer = UserSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data, status=HTTP_200_OK)

    @action(
        detail=True,
        methods=('post',),
        url_path='subscribe',
        url_name='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionSerializer(data={
            'follower': request.user.id, 'following': author.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        author_serializer = SubscriptionShowSerializer(
            author,
            context={'request': request}
        )
        return Response(author_serializer.data, status=HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        try:
            subscription = Subscription.objects.get(follower=request.user,
                                                    following=author)
            subscription.delete()
            return Response(status=HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            raise ParseError('Объект не найден')

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        url_name='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        authors = User.objects.filter(following__follower=request.user)
        paginator = FoodgramPagination()
        result_pages = paginator.paginate_queryset(
            queryset=authors, request=request
        )
        serializer = SubscriptionShowSerializer(
            result_pages, context={'request': request}, many=True
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=('delete',),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def update_avatar(self, request):
        user = request.user
        user.avatar = None
        user.save()
        return Response(status=HTTP_204_NO_CONTENT)

    @update_avatar.mapping.put
    def avatar(self, request):
        if 'avatar' not in request.data:
            return Response({'detail': 'Поле аватар обязательно.'},
                            status=HTTP_400_BAD_REQUEST)
        serializer = AvatarSerializer(request.user,
                                      data=request.data,
                                      partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
