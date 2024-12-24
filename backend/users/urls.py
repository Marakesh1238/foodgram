from django.urls import path
from .views import (AvatarDeleteView, AvatarUpdateView, CurrentUserView,
                    CustomUserDetailView, CustomUserListView)

urlpatterns = [
    path('users/', CustomUserListView.as_view(),
         name='user-list'),
    path('users/<int:id>/', CustomUserDetailView.as_view(),
         name='user-detail'),
    path('users/me/', CurrentUserView.as_view(),
         name='current-user'),
    path('users/me/avatar/', AvatarUpdateView.as_view(),
         name='avatar-update'),
    path('users/me/avatar/', AvatarDeleteView.as_view(),
         name='avatar-delete'),
]
