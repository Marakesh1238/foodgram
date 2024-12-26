from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AvatarDeleteView, AvatarUpdateView, CurrentUserView,
                    CustomUserDetailView,
                    SubscriptionViewSet)


router = DefaultRouter()
router.register(r'users/subscriptions', SubscriptionViewSet, basename='subscription')

user_urlpatterns = [
    path('users/<int:id>/', CustomUserDetailView.as_view(), name='user-detail'),
    path('users/me/', CurrentUserView.as_view(), name='current-user'),
]

avatar_urlpatterns = [
    path('users/me/avatar/', AvatarUpdateView.as_view(), name='avatar-update'),
    path('users/me/avatar/delete/', AvatarDeleteView.as_view(), name='avatar-delete'),
]

subscriptions_urlpatterns = [
    path('', include(router.urls)),
    path('users/<int:pk>/subscribe/', SubscriptionViewSet.as_view({'post': 'subscribe', 'delete': 'unsubscribe'}), name='user-subscribe'),
]

urlpatterns = user_urlpatterns + avatar_urlpatterns + subscriptions_urlpatterns
