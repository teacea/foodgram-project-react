from django.contrib.auth import get_user_model
from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from api.filters import IngredientSearchFilter, RecipeFilter
from recipes.models import (Ingredient, Recipe, ShoppingCart,
                            Subscribe, Tag, FavoriteRecipe)
from api.filters import RecipeFilter, IngredientSearchFilter
from api.mixins import CreateDestroyViewSet
from api.pagination import LimitPageNumberPagination
from api.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from api.serializers import SubscribeListSerializer, GetUserSerializer
                          

User = get_user_model()

class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = GetUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        if request.method == 'POST':
            serializer = SubscribeListSerializer(
                author,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            sub = get_object_or_404(Subscribe, user=user,
                                    author=author)
            sub.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        page = self.paginate_queryset(queryset)
        serializer = SubscribeListSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)