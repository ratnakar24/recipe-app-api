from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    default = {
        'title': 'Sample title',
        'time_minutes': 5,
        'price': 5.0
    }
    default.update(**params)
    return Recipe.objects.create(user=user, **default)


class PublicRecipeAPITests(TestCase):
    """Test publicly avilable Recipe API"""
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access recipe list"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test private Recipe API list"""
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'rsratna24@gmail.com',
            'simplepassword'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe_list(self):
        """Test retrieving recipe"""
        sample_recipe(self.user)
        sample_recipe(self.user)

        recipes = Recipe.objects.all().order_by('-id')

        serializer = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_user(self):
        """Test retrieving recipe list for authenticated user"""
        user2 = get_user_model().objects.create_user(
            'ratnakar@gmail.com',
            'sample123'
        )
        sample_recipe(user2)
        sample_recipe(self.user)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')

        serializer = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
