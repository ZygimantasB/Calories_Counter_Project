"""Nutrition math for composite products (recipes).

Pure functions over dicts or ProductIngredient objects so both the API and the
tests share one implementation. All results are Decimals rounded to 2 dp.
"""
from decimal import Decimal, ROUND_HALF_UP

MACROS = ('calories', 'protein', 'fat', 'carbohydrates')
_CENT = Decimal('0.01')


def _dec(value):
    return Decimal(str(value or 0))


def _get(obj, key):
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)


def _round(values):
    return {m: values[m].quantize(_CENT, rounding=ROUND_HALF_UP) for m in MACROS}


def ingredient_totals(ingredients):
    """Sum of macro × quantity over all ingredients (the whole batch)."""
    totals = {m: Decimal('0') for m in MACROS}
    for ingredient in ingredients:
        quantity = _dec(_get(ingredient, 'quantity'))
        for m in MACROS:
            totals[m] += _dec(_get(ingredient, m)) * quantity
    return _round(totals)


def per_serving(totals, servings_yield):
    """Batch totals divided by the number of servings the batch makes."""
    servings_yield = _dec(servings_yield)
    if servings_yield <= 0:
        raise ValueError('servings_yield must be greater than 0')
    return _round({m: _dec(totals[m]) / servings_yield for m in MACROS})


def scaled(per_serving_values, servings):
    """Per-serving values multiplied by the number of servings being logged."""
    servings = _dec(servings)
    if servings <= 0:
        raise ValueError('servings must be greater than 0')
    return _round({m: _dec(per_serving_values[m]) * servings for m in MACROS})


def _floats(values):
    return {m: float(values[m]) for m in MACROS}


def serialize_product(product):
    """JSON-ready representation shared by the API and the quick-add helpers."""
    ingredients = list(product.ingredients.all())
    totals = ingredient_totals(ingredients)
    return {
        'id': product.id,
        'name': product.name,
        'servings_yield': float(product.servings_yield),
        'ingredient_count': len(ingredients),
        'ingredients': [
            {
                'id': ing.id,
                'name': ing.name,
                **_floats({m: getattr(ing, m) for m in MACROS}),
                'quantity': float(ing.quantity),
            }
            for ing in ingredients
        ],
        'totals': _floats(totals),
        'per_serving': _floats(per_serving(totals, product.servings_yield)),
    }
