from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAG_URL = reverse('recipe:tag-list')


class PublicTagsAPITest(TestCase):
    """Test the publicly available tags api"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for listing tags"""
        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITest(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'rsratna24@gmail.com', 'simplepass'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAG_URL)

        tags = Tag.objects.all().order_by('-name')

        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_tags_limited_to_user(self):
        """Test that the tags returned are for the authenticated user"""
        user2 = get_user_model().objects.create_user(
            'ratna@gmail.com',
            'password'
        )
        Tag.objects.create(user=user2, name='Fruity')
        tag = Tag.objects.create(user=self.user, name='Comfort food')

        res = self.client.get(TAG_URL)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_tag(self):
        """Test that the tag is created successfully"""
        payload = {'name': 'Vegan'}
        self.client.post(TAG_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_tag_with_invalid_name(self):
        """Test that the tag is not created with empty name"""
        payload = {'name': ''}
        res = self.client.post(TAG_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipe(self):
        """Test retieving tags assigned to only recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Non Veg')
        tag2 = Tag.objects.create(user=self.user, name='Veg')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Chicken Biriyani',
            time_minutes=60,
            price=20.0
        )
        recipe.tags.add(tag1)
        res = self.client.get(TAG_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test Retrieving tags assigned to recipes are distintct"""
        tag = Tag.objects.create(user=self.user, name='Non veg')
        Tag.objects.create(user=self.user, name='Veg')

        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Chicken Biriyani',
            time_minutes=60,
            price=20.0
        )
        recipe1.tags.add(tag)

        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Chicken Curry',
            time_minutes=20,
            price=10.0
        )

        recipe2.tags.add(tag)

        res = self.client.get(TAG_URL, {'assigned_only': 1})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
