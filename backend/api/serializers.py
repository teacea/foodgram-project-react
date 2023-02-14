
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (FavoriteRecipe, Ingredient, QuanityRecepies, Recipe,
                            ShoppingCart, Tag, Subscribe)
from user.models import CustomUser
from djoser.serializers import UserSerializer, UserCreateSerializer


from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    ''''Запрос списка подписок'''
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class UserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
        required_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class QuanityIngredientsSerializer(serializers.ModelSerializer):
    '''Сериализатор для переходной таблицы'''
    id = serializers.ReadOnlyField(
        source='ingredient.id',
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name',
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = QuanityRecepies
        fields = ('id', 'name', 'measurement_unit', 'quanity')


class TagSerializer(serializers.ModelSerializer):
    '''Сериализатор для тегов'''
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    '''Сериализатор ингредиентов'''
    class Meta:
        fields = ('__all__')
        model = Ingredient


class IngredientEditSerializer(serializers.ModelSerializer):
    '''Сериализатор для изменения ингредиентов'''
    id = serializers.IntegerField()
    quanity = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'quanity')


class RecipeSerializer(serializers.ModelSerializer):
    '''Сериализатор для чтения Рецепта'''
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    image = serializers.CharField(source="image.url")
    ingredients = QuanityIngredientsSerializer(
        source='quanityrecipe_set',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'text',
                  'is_favorited', 'in_cart', 'author', 'image',
                  'cooking_time', 'name', 'pub_date')

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj.id).exists()
        return False

    def get_is_in_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj.id).exists()
        return False


class CreateRecipeSerializer(serializers.ModelSerializer):
    '''Сериализатор для создания и изменения рецепта'''
    author = serializers.PrimaryKeyRelatedField(
             read_only=True)
    image = Base64ImageField()
    ingredients = IngredientEditSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('__all__')



    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            QuanityRecepies.objects.bulk_create([
                QuanityRecepies(
                    recipe=recipe,
                    ingredient_id=ingredient.get('id'),
                    amount=ingredient.get('amount'),)
            ])
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)

    def validate(self, attrs):
        ingredients_list = set()
        tags_list = set()
        name = set()
        ingredient = attrs['ingredient']
        tag = attrs['tag']
        # Проверка названия рецепта 
        name = attrs.get('name')
        if len(name) < 4:
            raise serializers.ValidationError({
                'name': 'Название рецепта минимум 4 символа'})
        name.add(name)
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


class CropRecipeSerializer(serializers.ModelSerializer):
    '''Сериализатор для просмотра рецепта на главной'''
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    '''Сериализатор подписки'''
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
        model = Subscribe
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'following'),
                message='Уже подписан!'
            )
        ]


class SubscribeListSerializer(serializers.ModelSerializer):
    '''Сериализатор для вывода подписок'''
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
        return CropRecipeSerializer(
            recipes, many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='favorite_recipe.id',
    )
    name = serializers.ReadOnlyField(
        source='favorite_recipe.name',
    )
    image = serializers.CharField(
        source='favorite_recipe.image',
        read_only=True,
    )
    cooking_time = serializers.ReadOnlyField(
        source='favorite_recipe.cooking_time',
    )

    class Meta:
        model = FavoriteRecipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if FavoriteRecipe.objects.filter(user=user,
                                         favorite_recipe=recipe).exists():
            raise serializers.ValidationError({
                'errors': 'Рецепт уже в избранном'})
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='recipe.id',
    )
    name = serializers.ReadOnlyField(
        source='recipe.name',
    )
    image = serializers.CharField(
        source='recipe.image',
        read_only=True,
    )
    cooking_time = serializers.ReadOnlyField(
        source='recipe.cooking_time',
    )

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if ShoppingCart.objects.filter(user=user,
                                       recipe=recipe).exists():
            raise serializers.ValidationError({
                'errors': 'Рецепт уже добавлен в список покупок'})
        return data