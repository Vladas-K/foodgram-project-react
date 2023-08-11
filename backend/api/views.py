from django.db.models import Sum
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
                            IngredientRecipe, Recipe, ShoppingCart,
                            Tag)
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
        queryset = User.objects.filter(following__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowReadSerializer(
            pages, many=True, context={'request': request}
        )
        data = serializer.data
        for author in data:
            recipes = Recipe.objects.filter(author=author['id'])[:3]
            recipe_serializer = RecipeReadSerializer(recipes, many=True)
            author['recipes'] = recipe_serializer.data
        return self.get_paginated_response(data)

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

    def add_or_delete_object(
            self, request, pk, serializer_class, object_class):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            data = {
                'user': request.user.id,
                'recipe': recipe.id
            }
            serializer = serializer_class(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        get_object_or_404(
            object_class,
            user=request.user.id,
            recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('post', 'delete'),
        detail=True,
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def add_delete_favorite(self, request, pk):
        return self.add_or_delete_object(
            request, pk, FavoriteSerializer, Favorite)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated])
    def add_delete_shopping_cart(self, request, pk):
        return self.add_or_delete_object(
            request, pk, ShoppingCartSerializer, ShoppingCart)

    # @action(detail=False, url_path='download_shopping_cart')
    # def download_shopping_cart(self, request):
    #     ingredients = {}
    #     ingredients = IngredientRecipe.objects.filter(
    #         recipe__shopping_list__user=request.user
    #     ).values(
    #         'ingredient__name', 'ingredient__measurement_unit'
    #     ).annotate(total_amount=Sum('amount'))
    #     shopping_list = []
    #     for i, ingredient in enumerate(ingredients, start=1):
    #         name = ingredient['ingredient__name']
    #         total_amount = ingredient['total_amount']
    #         measurement_unit = ingredient['ingredient__measurement_unit']
    #         shopping_list.append(
    #             f"{i}. {name}  - {total_amount}{measurement_unit}.")
    #     return HttpResponse(
    #         '\n'.join(shopping_list), content_type='text/plain'
    #     )
    
    @action(detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_list__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by('ingredient__name')
        shopping_list = []
        for i, ingredient in enumerate(ingredients, start=1):
            name = ingredient['ingredient__name']
            total_amount = ingredient['total_amount']
            measurement_unit = ingredient['ingredient__measurement_unit']
            shopping_list.append(
                f"{i}. {name}  - {total_amount}{measurement_unit}.")
        return HttpResponse(
            '\n'.join(shopping_list), content_type='text/plain'
        )


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
