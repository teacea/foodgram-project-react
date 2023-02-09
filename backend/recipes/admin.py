from django.contrib import admin

from .models import Favorite, Ingredient, QuanityRecepies, Recipe, Tag

admin.site.register(QuanityRecepies)
admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Favorite)