import json
import logging
import google.generativeai as genai
from django.conf import settings
from google.api_core.exceptions import GoogleAPICallError, PermissionDenied, Unauthenticated, InvalidArgument, FailedPrecondition

logger = logging.getLogger('count_calories_app')

class GeminiService:
    @staticmethod
    def get_nutrition_info(food_name):
        """
        Fetches nutritional information for a given food name from Gemini AI.
        Returns a dictionary with success status and data or error.
        """
        if not food_name:
            return {'success': False, 'error': 'Food name is required', 'status': 400}

        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.error("Gemini API key is not configured on the server")
            return {'success': False, 'error': 'Gemini API key is not configured on the server', 'status': 500}

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        You are a nutrition expert. Analyze this food description: "{food_name}"
        
        IMPORTANT: Calculate nutritional values for the EXACT quantity mentioned in the description, not per 100g.
        
        If the description contains:
        - A specific quantity (like "150g", "2 pieces", "1 cup"), calculate for that exact amount
        - Multiple foods or a complex meal, sum up the nutrition from all components
        - Lithuanian or foreign language food names, identify the foods and provide accurate values
        - No specific quantity, assume a typical serving size for that food
        
        For complex meals like "italiÅ¡kas kapotos viÅ¡tienos maltinukas, Å¡vieÅ¾iÅ¾ darÅ¾oviÅ³ salotos, virtas bulguras (iLunch)", 
        break it down into components:
        - Italian chicken cutlet/meatballs
        - Fresh vegetable salad  
        - Cooked bulgur
        And sum the nutritional values of all components for a typical meal portion.
        
        Return ONLY this JSON format with no additional text:
        {{
            "product_name": "{food_name}",
            "calories": <total_calories_for_specified_amount>,
            "fat": <total_fat_grams_for_specified_amount>,
            "carbohydrates": <total_carbs_grams_for_specified_amount>,
            "protein": <total_protein_grams_for_specified_amount>
        }}
        
        Rules:
        - All values must be numbers (not strings)
        - Calculate for the ACTUAL quantity/serving mentioned, not per 100g
        - For complex meals, sum all components
        - If quantity is unclear, use realistic serving sizes
        - Fat, carbs, protein in grams; calories in kcal
        - Be accurate with Lithuanian food translations
        """

        try:
            response = model.generate_content(prompt)
        except (Unauthenticated, PermissionDenied) as e:
            logger.error(f"Gemini authentication error: {e}")
            return {'success': False, 'error': 'Invalid or unauthorized Gemini API key. Please check your API key configuration.', 'code': 'invalid_api_key', 'status': 401}
        except GoogleAPICallError as e:
            # Check if it's an API key validation error (400 status)
            error_message = str(e)
            if "API_KEY_INVALID" in error_message or "API key not valid" in error_message:
                logger.error(f"Invalid Gemini API key: {e}")
                return {
                    'success': False,
                    'error': 'Invalid Gemini API key. Please obtain a valid API key from https://aistudio.google.com/app/apikey and update it in your .env file.',
                    'code': 'invalid_api_key',
                    'status': 401
                }
            else:
                logger.error(f"Gemini API error: {e}")
                return {'success': False, 'error': 'Gemini service error. Please try again later.', 'code': 'gemini_api_error', 'status': 502}
        except (InvalidArgument, FailedPrecondition) as e:
            logger.error(f"Gemini API error: {e}")
            return {'success': False, 'error': 'Gemini service error. Please try again later.', 'code': 'gemini_api_error', 'status': 502}

        response_text = response.text.strip()

        try:
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            nutrition_data = json.loads(response_text.strip())

            required_fields = ['product_name', 'calories', 'fat', 'carbohydrates', 'protein']
            for field in required_fields:
                if field not in nutrition_data:
                    raise ValueError(f"Missing field: {field}")

            for field in ['calories', 'fat', 'carbohydrates', 'protein']:
                nutrition_data[field] = float(nutrition_data[field])

            return {
                'success': True,
                'data': nutrition_data
            }

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing Gemini response: {e}, Response: {response_text}")
            return {'success': False, 'error': 'Failed to parse nutritional information from AI response', 'status': 500}
