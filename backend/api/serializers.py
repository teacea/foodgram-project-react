from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, QuanityRecepies, Recipe,
                            ShoppingCart, Tag)
from user.models import CustomUser
from user.models import Follow
from djoser.serializers import UserSerializer

class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class FollowSerializer(serializers.ModelSerializer):
    following = serializers.SlugRelatedField(
        slug_field='id',
        queryset=CustomUser.objects.all()
    )
    user = serializers.SlugRelatedField(
        slug_field='id',
        queryset=CustomUser.objects.all(),
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message='Уже подписан!'
            )
        ]


class FollowListSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, user):
        current_user = self.context.get('current_user')
        other_user = user.following.all()
        if user.is_anonymous:
            return False
        if other_user.count() == 0:
            return False
        if Follow.objects.filter(user=user, following=current_user).exists():
            return True
        return False

    def get_recipes(self, obj):
        recipes = obj.recipes.all()[:3]
        request = self.context.get('request')
        return RecipeImageSerializer(
            recipes, many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('__all__')
        model = Ingredient


class CreateIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = QuanityRecepies
        fields = ('id', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=QuanityRecepies.objects.all(),
                fields=['ingredient', 'measurement_unit']
            )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    tag = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    image = serializers.CharField(source="image.url")
    ingredients = CreateIngredientsSerializer(
        source='quanityrecipe_set',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    in_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tag', 'ingredients', 'description',
                  'is_favorited', 'in_cart', 'author', 'image',
                  'cooking_time', 'name', 'pub_date')

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj.id).exists()
        return False

    def get_in_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj.id).exists()
        return False
    
    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            QuanityRecepies.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                quanity=ingredient.get('quanity')
            )

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            quanity=('quanityrecepies__quanity')
        )
        return ingredients


class CropRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr),
                               name=f'{uuid.uuid1()}.{ext}')

        return super().to_internal_value(data)


class CreateRecipeSerializer(serializers.ModelSerializer):
    tag = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    ingredients = CreateIngredientsSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name',
                  'text', 'cooking_time')
    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        QuanityRecepies.objects.filter(recipe=instance).delete()
        self.create_ingredients(recipe=instance, ingredients=ingredients)
        return instance

    @transaction.atomic
    def create_ingredients(self, recipe, ingredients):
        QuanityRecepies.objects.bulk_create([QuanityRecepies(
            ingredient=Ingredient.objects.get(id=ing['id']),
            recipe=recipe,
            quanity=ing['quanity']
        ) for ing in ingredients])

    def validate(self, attrs):
        ingredients_list = set()
        tags_list = set()
        ingredient = attrs['ingredient']
        tag = attrs['tag']

        # Проверка ингредиентов
        if not ingredient:
            raise ValidationError('В рецепте должен быть хотя бы'
                                  ' 1 ингридиент.')
        for ing in ingredient:
            ingredient = Ingredient.objects.get(id=ing['id'])
            if ingredient in ingredients_list:
                raise ValidationError('Игредиенты не могут повторяться')
            if ing['amount'] <= 0:
                raise ValidationError('Количество ингридиента не может'
                                      ' быть меньше 0')
            ingredients_list.add(ingredient)

        # Проверка тегов
        if not tag:
            raise ValidationError('Необходимо указать хотя бы 1 тег!')
        for tag in tag:
            if tag in tags_list:
                raise ValidationError('Теги должны быть уникальными!')
            tags_list.add(tag)

        if not attrs['cooking_time'] > 0:
            raise ValidationError('Время готовки не может'
                                  ' быть меньше 1 минуты!')

        return attrs

    def to_representation(self, instance):
        return RecipeSerializer(instance,
                                context={'request':
                                         self.context.get('request')}).data