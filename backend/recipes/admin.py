from django.contrib import admin

from .models import (Subscribe, Ingredient, IngredientAmount,
                     Recipe, Tag, FavoriteRecipe)


class IngredientAmountAdmin(admin.StackedInline):
    model = IngredientAmount
    autocomplete_fields = ('ingredient',)
    min_num = 1
    extra = 0

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'added_to_favorites')
    search_fields = ('name', 'author__email', 'tag__name')
    inlines = (IngredientAmountAdmin,)

    @admin.display(description='Количество в избранных у пользователя')
    def added_to_favorites(self, obj):
        return FavoriteRecipe.objects.filter(recipe=obj).count()
        


@admin.register(Ingredient)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(Tag)
admin.site.register(Subscribe)