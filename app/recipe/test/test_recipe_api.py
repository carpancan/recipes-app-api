from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Ingredient, Tag

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 4,
        'price': 5.00,
    }

    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def sample_tag(user, name='Sample Tag'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Sample Ingredient'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


class PublicRecipeApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(RECIPES_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@user.com',
            'Passp5523445'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-title')

        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipes_limited_to_user(self):

        user2 = get_user_model().objects.create_user(
            'test2@user.com',
            'pass9876'
        )

        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(len(serializer.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_view_recipe_detail(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        response = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(response.data, serializer.data)

    def test_create_basic_recipe(self):
        payload = {
            'title': 'Chocolate cheescake',
            'time_minutes': 30,
            'price': 5.00
        }

        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])

        self.assertEqual(payload['title'], recipe.title)
        self.assertEqual(payload['time_minutes'], recipe.time_minutes)
        self.assertEqual(payload['price'], recipe.price)

    def test_create_recipe_with_tags(self):
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Dessert')

        payload = {
            'title': 'Avocado lime chesscake',
            'time_minutes': 60,
            'price': 20.00,
            'tags': [tag1.id, tag2.id]
        }

        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])
        tags = Tag.objects.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

        self.assertIn(tag1, recipe.tags.all())
        self.assertIn(tag2, recipe.tags.all())

    def test_create_recipe_with_ingredients(self):
        ingredient1 = sample_ingredient(user=self.user, name='Chocolat')
        ingredient2 = sample_ingredient(user=self.user, name='Wine')

        payload = {
            'title': 'Avocado lime chesscake',
            'time_minutes': 60,
            'price': 20.00,
            'ingredients': [ingredient1.id, ingredient2.id]
        }

        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])
        ingredients = Ingredient.objects.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

        self.assertIn(ingredient1, recipe.ingredients.all())
        self.assertIn(ingredient2, recipe.ingredients.all())

    def test_update_partial_recipe(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Carrots')

        payload = {
            'title': 'Carrots sauce',
            'tags': [new_tag.id]
        }
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(len(recipe.tags.all()), len(payload['tags']))

    def test_full_update_recipe(self):
        ingredient1 = sample_ingredient(user=self.user, name='Chocolat')
        ingredient2 = sample_ingredient(user=self.user, name='Wine')

        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Dessert')

        payload = {
            'title': 'Avocado lime chesscake',
            'time_minutes': 60,
            'price': 20.00,
            'ingredients': [ingredient1.id, ingredient2.id],
            'tags': [tag1.id, tag2.id],
            'link': 'http://localhost:8000'
        }

        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe_id = response.data['id']

        new_ingredient1 = sample_ingredient(user=self.user, name='Vinegar')
        new_ingredient2 = sample_ingredient(user=self.user, name='Salt')

        new_tag1 = Tag.objects.create(user=self.user, name='Meat')
        new_tag2 = Tag.objects.create(user=self.user, name='Fish')

        new_payload = {
            'title': 'Test recipe',
            'time_minutes': 120,
            'price': 25.00,
            'ingredients': [new_ingredient1.id, new_ingredient2.id],
            'tags': [new_tag1.id, new_tag2.id],
            'link': 'http://0.0.0.0:8000'
        }
        url = detail_url(recipe_id)
        new_response = self.client.put(url, new_payload)

        self.assertEqual(new_response.status_code, status.HTTP_200_OK)

        recipe = Recipe.objects.get(id=recipe_id)
        self.assertEqual(new_payload['title'], recipe.title)
        self.assertEqual(new_payload['time_minutes'], recipe.time_minutes)
        self.assertEqual(new_payload['price'], recipe.price)
        self.assertEqual(new_payload['link'], recipe.link)
        self.assertEqual(len(new_payload['ingredients']),
                         len(recipe.ingredients.all()))
        self.assertEqual(len(new_payload['tags']),
                         len(recipe.tags.all()))

        self.assertNotEqual(payload['title'], recipe.title)
        self.assertNotEqual(payload['time_minutes'], recipe.time_minutes)
        self.assertNotEqual(payload['price'], recipe.price)
        self.assertNotEqual(payload['link'], recipe.link)
        self.assertNotIn(payload['ingredients'][0], recipe.ingredients.all())
        self.assertNotIn(payload['tags'][0], recipe.tags.all())
