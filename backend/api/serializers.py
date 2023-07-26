from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (CharField, IntegerField,
                                        ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        ReadOnlyField, SerializerMethodField)

from recipes.models import (Favorite, Follow, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)
from .validators import (validate_favorite, validate_recipe,
                         validate_shopping_cart, validate_subscription)

User = get_user_model()


class UserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password', 'is_subscribed', )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, author=obj).exists()

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.password = make_password(validated_data["password"])
        user.save()
        return user


class FollowSerializer(ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        return validate_subscription(self, data)

    def to_representation(self, instance):
        author = instance.author
        context = self.context
        request = context.get('request')
        serializer_context = {'request': request}
        serializer = FollowReadSerializer(author, context=serializer_context)
        return serializer.data


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', )


class IngredientRecipeWriteSerializer(ModelSerializer):

    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class IngredientRecipeSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeReadSerializer(ModelSerializer):
    author = UserSerializer(read_only=True, many=False)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientSerializer(read_only=True, many=True)
    image = Base64ImageField(max_length=None)
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.in_favorite.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.shopping_list.filter(user=request.user).exists()


class FollowReadSerializer(ModelSerializer):
    recipes = RecipeReadSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'recipes', 'recipes_count'
        )

    def get_recipes_count(self, author):
        return Recipe.objects.filter(author=author).count()


class RecipeCreateSerializer(ModelSerializer):
    image = Base64ImageField(max_length=None)
    ingredients = IngredientRecipeWriteSerializer(
        many=True,
    )
    tags = PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(),
    )
    image = Base64ImageField(max_length=None)
    author = UserSerializer(read_only=True)
    cooking_time = IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',)

    def validate(self, data):
        return validate_recipe(self, data)

    def add_tags(self, instance, tags):
        for tag in tags:
            current_tag, status = Tag.objects.get_or_create(name=tag)
            instance.tags.add(current_tag)

    def add_ingredients(self, instance, ingredients):
        IngredientRecipe.objects.filter(recipe=instance).delete()
        ingredient_list = [
            IngredientRecipe(
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'],
                recipe=instance,
            )
            for ingredient_data in ingredients
        ]
        IngredientRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        self.add_tags(recipe, tags)
        self.add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        super().update(instance, validated_data)
        instance.tags.clear()
        self.add_tags(instance, tags)
        self.add_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        context = self.context
        request = context.get('request')
        serializer_context = {'request': request}
        serializer = RecipeReadSerializer(instance, context=serializer_context)
        return serializer.data


class ShoppingCartSerializer(ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def validate(self, data):
        return validate_shopping_cart(self, data)

    def to_representation(self, instance):
        recipe = instance.recipe
        context = self.context
        request = context.get('request')
        serializer_context = {'request': request}
        serializer = RecipeReadSerializer(recipe, context=serializer_context)
        return serializer.data


class FavoriteSerializer(ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def validate(self, data):
        return validate_favorite(self, data)

    def to_representation(self, instance):
        recipe = instance.recipe
        context = self.context
        request = context.get('request')
        serializer_context = {'request': request}
        serializer = RecipeReadSerializer(recipe, context=serializer_context)
        return serializer.data
