from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def get_recipe_detail_url(recipe_id):
    """Return recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Fuity'):
    """Create and returns a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create and returns a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and returns a sample recipe"""
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

    def test_retrieve_receipe_detail(self):
        """Test retrieving recipe detail for authenticated user"""
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        recipe.ingredients.add(sample_ingredient(self.user))

        serializer = RecipeDetailSerializer(recipe)

        url = get_recipe_detail_url(recipe.id)

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Chocolate cake',
            'time_minutes': 5,
            'price': 60.0
        }

        res = self.client.post(RECIPE_URL, payload)

        recipe = Recipe.objects.get(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating recipe with tags"""
        tag1 = sample_tag(self.user, name='Vegan')
        tag2 = sample_tag(self.user, name='Dessert')

        payload = {
            'title': 'New chocolate lime cake',
            'time_minutes': 5,
            'price': 60.0,
            'tags': [tag1.id, tag2.id]
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        tags = recipe.tags.all()

        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)
        self.assertEqual(tags.count(), 2)

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        ingredient1 = sample_ingredient(self.user, name='Prawns')
        ingredient2 = sample_ingredient(self.user, name='Ginger')

        payload = {
            'title': 'Prawn manchurian',
            'time_minutes': 60,
            'price': 25.0,
            'ingredients': [ingredient1.id, ingredient2.id]
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_create_recipe_with_tags_and_ingredients(self):
        """Test creating recipe with both tags and ingredients"""
        tag1 = sample_tag(self.user, name='Chicken dishes')
        tag2 = sample_tag(self.user, name='Non veg')

        ingredient1 = sample_ingredient(self.user, name='Garlic')
        ingredient2 = sample_ingredient(self.user, name='Masala')

        payload = {
            'title': 'Chicken Curry',
            'time_minutes': 60,
            'price': 200.0,
            'tags': [tag1.id, tag2.id],
            'ingredients': [ingredient1.id, ingredient2.id],
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        tags = recipe.tags.all()
        ingredients = recipe.ingredients.all()

        self.assertEqual(tags.count(), 2)
        self.assertEqual(ingredients.count(), 2)

        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe model using patch"""
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        new_tag = sample_tag(self.user, 'Different tag')
        payload = {
            'title': 'Different title',
            'time_minutes': 10,
            'price': 20.0,
            'tags': [new_tag.id]
        }
        url = get_recipe_detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        tags = recipe.tags.all()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """test updating a recipe model using put"""
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))

        payload = {
            'title': 'Different title',
            'time_minutes': 5,
            'price': 10.0
        }
        url = get_recipe_detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()

        tags = recipe.tags.all()

        self.assertEqual(len(tags), 0)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
