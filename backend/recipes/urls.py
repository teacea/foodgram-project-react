

from django.urls import include, path
from recipes.views import IngredientsViewSet, RecipeViewSet, TagViewSet
from rest_framework.routers import DefaultRouter

app_name = 'recipes'

router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('ingredients', IngredientsViewSet)
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]