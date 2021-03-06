from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsAPITests(TestCase):
    """Test public ingredients api"""
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for calling ingredients api"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """Test private ingredients api"""
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'rsratna24@gmail.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Test retrieving ingredients"""
        Ingredient.objects.create(user=self.user, name='Salt')
        Ingredient.objects.create(user=self.user, name='Pepper')

        ingredients = Ingredient.objects.all().order_by('-name')

        res = self.client.get(INGREDIENTS_URL)

        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retieve_ingredients_limited_to_user(self):
        """Test retrieved ingredients are for authenticated user"""
        user2 = get_user_model().objects.create_user(
            'other@gmail.com',
            'testpass'
        )

        Ingredient.objects.create(user=user2, name='Vinegar')
        ingredient = Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredients_successful(self):
        """Test that the ingredients are created"""
        payload = {'name': 'Vinegar'}

        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredients_with_invalid_name(self):
        """Test ingredient creation fails with empty name"""
        payload = {'name': ''}

        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assinged_to_recipe(self):
        """Test retrive ingredients that are assigned to recipe"""
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name='Chicken'
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name='Rice'
        )

        recipe = Recipe.objects.create(
            user=self.user,
            title='Chicken Biriyani',
            time_minutes=60,
            price=20.0
        )
        recipe.ingredients.add(ingredient1)

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assinged_unique(self):
        """Test retirve ingredients assigned are unique"""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Chicken'
        )
        Ingredient.objects.create(user=self.user, name='Alooo')

        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Chicken Curry',
            time_minutes=60,
            price=20.0
        )
        recipe1.ingredients.add(ingredient)

        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Chicken Biriyani',
            time_minutes=60,
            price=20.0
        )

        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
