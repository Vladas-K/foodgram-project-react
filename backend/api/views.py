from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Follow, Ingredient,
                            Recipe, ShoppingCart, Tag)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteSerializer, FollowReadSerializer,
                          FollowSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeReadSerializer,
                          ShoppingCartSerializer, TagSerializer,
                          UserSerializer)

User = get_user_model()


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=False,
        url_path='subscriptions',
        permission_classes=[IsAuthenticated],
    )
    def get_subscriptions(self, request):
        # Нужны только последние пять котиков белого цвета
        subscriptions = User.objects.filter(following__user=request.user)[:3]
        # Передадим queryset cats сериализатору
        # и разрешим работу со списком объектов
        serializer = FollowReadSerializer(subscriptions, many=True, context={
            'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=['post', 'delete'], detail=True,
        url_path='subscribe',
        permission_classes=[IsAuthenticated],
    )
    def add_delete_subscription(self, request, id):
        if request.method == 'POST':
            serializer = FollowSerializer(
                data={
                    'user': request.user.id,
                    'author': get_object_or_404(User, id=id).id
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            subscription = get_object_or_404(
                Follow,
                author=get_object_or_404(User, id=id),
                user=request.user
            )
            self.perform_destroy(subscription)
            return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    permission_classes = (IsAuthorOrReadOnly, )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(
        methods=('get',),
        detail=False,
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def get_favorite(self, request):
        favorites = self.filter_queryset(
            self.queryset).filter(in_favorite__user=request.user)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)

    @action(
        methods=('post', 'delete'),
        detail=True,
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def add_delete_favorite(self, request, pk):
        context = {"request": request}
        recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        if request.method == 'POST':
            serializer = FavoriteSerializer(data=data, context=context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            get_object_or_404(
                Favorite,
                user=request.user,
                recipe=get_object_or_404(Recipe, id=pk)
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)
        ingredients = {}
        for cart in shopping_cart:
            for ingredient_recipe in cart.recipe.ingredienttorecipe.all():
                ingredient = ingredient_recipe.ingredient
                if ingredient.name in ingredients:
                    ingredients[ingredient.name] += ingredient_recipe.amount
                else:
                    ingredients[ingredient.name] = ingredient_recipe.amount
        shopping_list = []
        for i, (name, amount) in enumerate(ingredients.items(), start=1):
            measurement_unit = Ingredient.objects.get(
                name=name).measurement_unit
            shopping_list.append(f"{i}. {name}  - {amount}{measurement_unit}.")
        return HttpResponse(
            '\n'.join(shopping_list), content_type='text/plain'
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated])
    def add_delete_shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            data = {
                'user': request.user.id,
                'recipe': recipe.id
            }
            serializer = ShoppingCartSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            get_object_or_404(
                ShoppingCart,
                user=request.user.id,
                recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    filter_backends = (IngredientFilter, )
    pagination_class = None
    search_fields = ('^name', )


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    pagination_class = None
