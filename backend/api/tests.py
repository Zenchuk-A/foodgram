from http import HTTPStatus

from django.test import Client, TestCase


class ListAPITestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_recipes_list_exists(self):
        """Проверка доступности списка рецептов."""
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tags_list_exists(self):
        """Проверка доступности списка рецептов."""
        response = self.client.get('/api/tags/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_ingredients_list_exists(self):
        """Проверка доступности списка рецептов."""
        response = self.client.get('/api/ingredients/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
