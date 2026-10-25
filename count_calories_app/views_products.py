"""Composite products (recipes): JSON API shared by the Django and React frontends."""
import json
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import FoodItem, Product, ProductIngredient
from .products import MACROS, ingredient_totals, per_serving, scaled, serialize_product

logger = logging.getLogger(__name__)

# Per-ingredient input limits (protein/fat/carbs fields hold max 999.99).
INGREDIENT_LIMITS = {
    'calories': Decimal('50000'),
    'protein': Decimal('999.99'),
    'fat': Decimal('999.99'),
    'carbohydrates': Decimal('999.99'),
}
# Capacity of the FoodItem diary columns a logged product is written into.
FOOD_ITEM_LIMITS = {
    'calories': Decimal('99999.99'),
    'protein': Decimal('999.99'),
    'fat': Decimal('999.99'),
    'carbohydrates': Decimal('999.99'),
}
MAX_INGREDIENTS = 50
_CENT = Decimal('0.01')


def _to_decimal(value):
    """Parse a finite Decimal rounded to 2 dp, or None when the value is not a number."""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not number.is_finite():
        return None
    return number.quantize(_CENT, rounding=ROUND_HALF_UP)


def _json_body(request):
    try:
        data = json.loads(request.body or b'{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _error(message, status=400):
    return JsonResponse({'success': False, 'error': message}, status=status)


def _limit_errors(values, prefix):
    return [
        f'{prefix} {m} ({values[m]}) exceeds the food diary limit of {FOOD_ITEM_LIMITS[m]}'
        for m in MACROS if values[m] > FOOD_ITEM_LIMITS[m]
    ]


def _validate_product_data(data, product_id=None):
    """Validate a product payload and return (is_valid, errors, sanitized)."""
    errors = []
    sanitized = {}

    name = str(data.get('name') or '').strip()
    if not name:
        errors.append('Product name is required')
    elif len(name) > 200:
        errors.append('Product name must be 200 characters or less')
    elif Product.objects.filter(name__iexact=name).exclude(pk=product_id).exists():
        errors.append(f'A product named "{name}" already exists')
    sanitized['name'] = name

    servings_yield = _to_decimal(data.get('servings_yield', 1))
    if servings_yield is None or servings_yield <= 0 or servings_yield > 100:
        errors.append('Servings yield must be greater than 0 and at most 100')
    sanitized['servings_yield'] = servings_yield

    raw_ingredients = data.get('ingredients')
    if not isinstance(raw_ingredients, list) or not raw_ingredients:
        errors.append('At least one ingredient is required')
        raw_ingredients = []
    elif len(raw_ingredients) > MAX_INGREDIENTS:
        errors.append(f'A product can have at most {MAX_INGREDIENTS} ingredients')
        raw_ingredients = []

    ingredients = []
    for index, item in enumerate(raw_ingredients, start=1):
        if not isinstance(item, dict):
            errors.append(f'Ingredient {index} is invalid')
            continue
        ingredient_name = str(item.get('name') or '').strip()
        if not ingredient_name:
            errors.append(f'Ingredient {index}: name is required')
        elif len(ingredient_name) > 200:
            errors.append(f'Ingredient {index}: name must be 200 characters or less')
        clean = {'name': ingredient_name}
        for m in MACROS:
            value = _to_decimal(item.get(m) or 0)
            if value is None or value < 0 or value > INGREDIENT_LIMITS[m]:
                errors.append(f'Ingredient {index}: {m} must be between 0 and {INGREDIENT_LIMITS[m]}')
            clean[m] = value
        quantity = _to_decimal(item.get('quantity', 1))
        if quantity is None or quantity <= 0 or quantity > 1000:
            errors.append(f'Ingredient {index}: quantity must be greater than 0 and at most 1000')
        clean['quantity'] = quantity
        ingredients.append(clean)
    sanitized['ingredients'] = ingredients

    if not errors:
        serving = per_serving(ingredient_totals(ingredients), servings_yield)
        errors.extend(_limit_errors(serving, 'Per-serving'))

    return len(errors) == 0, errors, sanitized


def _save_ingredients(product, ingredients):
    ProductIngredient.objects.bulk_create([
        ProductIngredient(product=product, order=order, **ingredient)
        for order, ingredient in enumerate(ingredients)
    ])


def _parse_log_date(value):
    """YYYY-MM-DD → that day at the current time (same rule as api_add_food); otherwise now."""
    if value:
        try:
            day = datetime.strptime(str(value), '%Y-%m-%d').date()
            return timezone.make_aware(datetime.combine(day, datetime.now().time()))
        except ValueError:
            pass
    return timezone.now()


@require_http_methods(["GET"])
def api_products(request):
    """List all composite products with totals and per-serving macros."""
    products = Product.objects.prefetch_related('ingredients')
    return JsonResponse({'products': [serialize_product(p) for p in products]})


@require_http_methods(["POST"])
def api_add_product(request):
    """Create a composite product from a JSON payload."""
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body')
    is_valid, errors, clean = _validate_product_data(data)
    if not is_valid:
        return _error('; '.join(errors))
    with transaction.atomic():
        product = Product.objects.create(name=clean['name'], servings_yield=clean['servings_yield'])
        _save_ingredients(product, clean['ingredients'])
    return JsonResponse({'success': True, 'product': serialize_product(product)})


@require_http_methods(["PUT", "PATCH"])
def api_update_product(request, product_id):
    """Replace a product's name, yield and full ingredient list."""
    product = Product.objects.filter(pk=product_id).first()
    if product is None:
        return _error('Product not found', status=404)
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body')
    is_valid, errors, clean = _validate_product_data(data, product_id=product.id)
    if not is_valid:
        return _error('; '.join(errors))
    with transaction.atomic():
        product.name = clean['name']
        product.servings_yield = clean['servings_yield']
        product.save()
        product.ingredients.all().delete()
        _save_ingredients(product, clean['ingredients'])
    return JsonResponse({'success': True, 'product': serialize_product(product)})


@require_http_methods(["DELETE"])
def api_delete_product(request, product_id):
    """Delete a product. Diary entries already logged from it are kept."""
    deleted, _ = Product.objects.filter(pk=product_id).delete()
    if not deleted:
        return _error('Product not found', status=404)
    return JsonResponse({'success': True})


@require_http_methods(["POST"])
def api_log_product(request, product_id):
    """Log N servings of a product as ONE FoodItem with summed macros."""
    product = Product.objects.prefetch_related('ingredients').filter(pk=product_id).first()
    if product is None:
        return _error('Product not found', status=404)
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body')

    servings = _to_decimal(data.get('servings', 1))
    if servings is None or servings <= 0 or servings > 100:
        return _error('Servings must be greater than 0 and at most 100')

    values = scaled(per_serving(ingredient_totals(product.ingredients.all()), product.servings_yield), servings)
    errors = _limit_errors(values, 'Logged')
    if errors:
        return _error('; '.join(errors))

    food = FoodItem.objects.create(
        product_name=product.name,
        consumed_at=_parse_log_date(data.get('date')),
        **values,
    )
    return JsonResponse({
        'success': True,
        'id': food.id,
        'food': {
            'id': food.id,
            'name': food.product_name,
            'calories': float(food.calories),
            'protein': float(food.protein),
            'carbs': float(food.carbohydrates),
            'fat': float(food.fat),
            'consumed_at': food.consumed_at.isoformat(),
        },
    })


def product_quick_entries(query='', limit=5):
    """Products shaped like quick-add/search rows (per-serving macros, 'carbs' key)."""
    products = Product.objects.prefetch_related('ingredients').order_by('-updated_at')
    if query:
        products = products.filter(name__icontains=query)
    entries = []
    for product in products[:limit]:
        data = serialize_product(product)
        serving = data['per_serving']
        entries.append({
            'id': f'product-{product.id}',
            'name': product.name,
            'calories': serving['calories'],
            'protein': serving['protein'],
            'carbs': serving['carbohydrates'],
            'fat': serving['fat'],
            'is_product': True,
            'product_id': product.id,
            'servings_yield': data['servings_yield'],
        })
    return entries
