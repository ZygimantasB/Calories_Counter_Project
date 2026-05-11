import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from count_calories_app.services import GeminiService
from google.genai import errors as genai_errors

class GeminiServiceTestCase(TestCase):
    def setUp(self):
        self.food_name = "Apple"
        self.mock_response_data = {
            "product_name": "Apple",
            "calories": 95,
            "fat": 0.3,
            "carbohydrates": 25,
            "protein": 0.5
        }
        self.mock_response_text = json.dumps(self.mock_response_data)

    @patch('count_calories_app.services.genai')
    def test_get_nutrition_info_success(self, mock_genai):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = self.mock_response_text
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        with self.settings(GEMINI_API_KEY='fake-api-key'):
            result = GeminiService.get_nutrition_info(self.food_name)

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], self.mock_response_data)
        mock_genai.Client.assert_called_with(api_key='fake-api-key')
        mock_client.models.generate_content.assert_called_once()

    def test_get_nutrition_info_no_food_name(self):
        result = GeminiService.get_nutrition_info("")
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 400)
        self.assertEqual(result['error'], 'Food name is required')

    @patch('count_calories_app.services.genai')
    def test_get_nutrition_info_no_api_key(self, mock_genai):
        with self.settings(GEMINI_API_KEY=None):
            result = GeminiService.get_nutrition_info(self.food_name)

        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 500)
        self.assertIn('not configured', result['error'])

    @patch('count_calories_app.services.genai')
    def test_get_nutrition_info_api_error(self, mock_genai):
        mock_client = MagicMock()
        api_error = genai_errors.APIError(
            401,
            {'error': {'message': 'Invalid API key', 'status': 'UNAUTHENTICATED'}},
        )
        mock_client.models.generate_content.side_effect = api_error
        mock_genai.Client.return_value = mock_client

        with self.settings(GEMINI_API_KEY='fake-api-key'):
            result = GeminiService.get_nutrition_info(self.food_name)

        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 401)
        self.assertEqual(result['code'], 'invalid_api_key')

    @patch('count_calories_app.services.genai')
    def test_get_nutrition_info_malformed_response(self, mock_genai):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Not JSON"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        with self.settings(GEMINI_API_KEY='fake-api-key'):
            result = GeminiService.get_nutrition_info(self.food_name)

        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 500)
        self.assertIn('Failed to parse', result['error'])
