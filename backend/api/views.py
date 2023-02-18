from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                            Tag)
from django.db.models import Sum
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (CropRecipeSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          TagSerializer)


class TagViewSet(ReadOnlyModelViewSet):
    '''Вьюсет для тегов'''
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientsViewSet(ReadOnlyModelViewSet):
    '''Вьюсет для ингредиентов'''
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,),)
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_obj(FavoriteRecipe, request.user, pk)
        if request.method == 'DELETE':
            return self.delete_obj(FavoriteRecipe, request.user, pk)
        return None

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.add_obj(ShoppingCart, request.user, pk)
        if request.method == 'DELETE':
            return self.delete_obj(ShoppingCart, request.user, pk)
        return None

    def add_obj(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({
                'errors': 'Рецепт уже добавлен в список'
            }, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = CropRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Рецепт уже удален'
        }, status=status.HTTP_400_BAD_REQUEST)

    def download_shopping_cart(self, request):
        user = request.user
        if not ShoppingCart.objects.filter(user=user).exists():
            return Response({'error': 'В корзине ничего нет!'},
                            status=status.HTTP_400_BAD_REQUEST)

        text = 'Список покупок:\n\n'
        ingredient_name = 'recipe__recipe__ingredient__name'
        ingredient_unit = 'recipe__recipe__ingredient__measurement_unit'
        recipe_amount = 'recipe__recipe__amount'
        amount_sum = 'recipe__recipe__amount__sum'
        cart = user.shopping_cart.select_related('recipe').values(
            ingredient_name, ingredient_unit).annotate(Sum(
                recipe_amount)).order_by(ingredient_name)
        for _ in cart:
            text += (
                f'{_[ingredient_name]} ({_[ingredient_unit]})'
                f' — {_[amount_sum]}\n'
            )
        response = HttpResponse(text, content_type='text/plain')
        filename = 'shopping_list.txt'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
