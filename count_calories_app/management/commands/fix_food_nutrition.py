"""Repair food rows that share a product_name but carry divergent nutrition.

Because quick-add and search used to report the *average* of every row sharing
a name -- and re-saved that average as a new row -- a name whose nutrition was
looked up twice ended up with several profiles, plus fabricated blends of them.
This command rewrites the values in place so one name means one nutrition.

    # See which names disagree with themselves
    python manage.py fix_food_nutrition --list-conflicts

    # Preview, then apply
    python manage.py fix_food_nutrition --name "Bananas (1)" \
        --calories 105 --protein 1.3 --fat 0.4 --carbs 27 --dry-run
    python manage.py fix_food_nutrition --name "Bananas (1)" \
        --calories 105 --protein 1.3 --fat 0.4 --carbs 27

Rows are only ever updated, never deleted.
"""

import json
import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from count_calories_app.models import FoodItem

NUTRITION_FIELDS = ('calories', 'protein', 'fat', 'carbohydrates')


def _profile(item):
    """The nutrition tuple identifying one variant of a product name."""
    return tuple(
        None if getattr(item, f) is None else Decimal(str(getattr(item, f)))
        for f in NUTRITION_FIELDS
    )


def find_conflicts():
    """Names logged with more than one distinct nutrition profile."""
    variants = defaultdict(lambda: defaultdict(int))
    for item in FoodItem.objects.all().only('product_name', *NUTRITION_FIELDS):
        variants[item.product_name][_profile(item)] += 1

    conflicts = []
    for name, profiles in variants.items():
        if len(profiles) < 2:
            continue
        conflicts.append({
            'product_name': name,
            'total_rows': sum(profiles.values()),
            'variants': [
                {
                    **{f: (None if v is None else float(v))
                       for f, v in zip(NUTRITION_FIELDS, profile)},
                    'rows': count,
                }
                for profile, count in sorted(
                    profiles.items(), key=lambda kv: kv[1], reverse=True
                )
            ],
        })
    conflicts.sort(key=lambda c: c['total_rows'], reverse=True)
    return conflicts


# Quick-add used to round calories to a whole number and macros to one decimal
# before the UI wrote them back, so a rounding twin can differ by at most half
# a unit of the last kept digit.
ROUNDING_TOLERANCE = {
    'calories': Decimal('0.5'),
    'protein': Decimal('0.05'),
    'fat': Decimal('0.05'),
    'carbohydrates': Decimal('0.05'),
}


def _is_rounding_drift(profiles):
    """True if every variant is within one rounding step of the others."""
    for index, field in enumerate(NUTRITION_FIELDS):
        values = [p[index] for p in profiles]
        if any(v is None for v in values):
            return False
        if max(values) - min(values) > ROUNDING_TOLERANCE[field]:
            return False
    return True


def _precision(profile):
    """Total number of significant decimal places across a profile."""
    total = 0
    for value in profile:
        if value is None:
            continue
        total += max(0, -value.normalize().as_tuple().exponent)
    return total


def _most_precise(profiles):
    """The variant that retains the most decimals; row count breaks ties."""
    return max(profiles.items(), key=lambda kv: (_precision(kv[0]), kv[1]))[0]



# Physical limits. Pure fat is the most energy-dense thing edible, at 900
# kcal/100g; nothing real exceeds it.
MAX_KCAL_PER_100G = 900
ATWATER = (('protein', 4), ('carbohydrates', 4), ('fat', 9))
GRAMS_IN_NAME = re.compile(r'(\d+(?:[.,]\d+)?)\s*g\b', re.IGNORECASE)


def _stated_grams(name):
    """Total grams a product name declares, or None if it declares none.

    Names often list components ('lašiniai 80 g. 150 g. juoda duona'), so the
    weights are summed -- taking only the first would understate the portion
    and raise a false alarm about energy density.
    """
    found = GRAMS_IN_NAME.findall(name)
    if not found:
        return None
    total = sum(float(g.replace(',', '.')) for g in found)
    return total or None


def audit_nutrition():
    """Physics-based problems in the current data, grouped by kind."""
    impossible, atwater, density = [], [], []

    seen = set()
    for item in FoodItem.objects.all().only('product_name', *NUTRITION_FIELDS):
        key = (item.product_name, _profile(item))
        if key in seen:
            continue
        seen.add(key)

        name = item.product_name
        cal = float(item.calories or 0)
        macros = {f: float(getattr(item, f) or 0) for f, _ in ATWATER}
        rows = FoodItem.objects.filter(product_name=name, **{
            f: getattr(item, f) for f in NUTRITION_FIELDS
        }).count()

        if cal > 0:
            for field, factor in ATWATER:
                energy = macros[field] * factor
                if energy > cal * 1.10:
                    impossible.append((name, rows,
                                       f'{field} alone is {energy:.0f} kcal, '
                                       f'more than the {cal:.0f} kcal stated'))

            macro_total = sum(macros[f] * factor for f, factor in ATWATER)
            if abs(macro_total - cal) > max(cal * 0.25, 30):
                atwater.append((name, rows,
                                f'macros total {macro_total:.0f} kcal but '
                                f'{cal:.0f} kcal is stated'))

            grams = _stated_grams(name)
            if grams and grams >= 10:
                per_100 = cal / grams * 100
                if per_100 > MAX_KCAL_PER_100G:
                    density.append((name, rows,
                                    f'{per_100:.0f} kcal/100g, above the '
                                    f'{MAX_KCAL_PER_100G} kcal/100g of pure fat'))

    return {'impossible': impossible, 'atwater': atwater, 'density': density}


class Command(BaseCommand):
    help = 'Normalize nutrition values for food entries sharing a product name.'

    def add_arguments(self, parser):
        parser.add_argument('--name', help='Exact product_name to normalize.')
        parser.add_argument('--calories', help='Correct calories (kcal).')
        parser.add_argument('--protein', help='Correct protein (g).')
        parser.add_argument('--fat', help='Correct fat (g).')
        parser.add_argument('--carbs', help='Correct carbohydrates (g).')
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would change without writing.')
        parser.add_argument('--list-conflicts', action='store_true',
                            help='List names logged with divergent nutrition.')
        parser.add_argument('--audit', action='store_true',
                            help='Report values that are implausible on their own '
                                 'terms, whether or not they conflict.')
        parser.add_argument('--fix-rounding-drift', action='store_true',
                            help='Collapse variants that differ only by display '
                                 'rounding onto their most precise value.')
        parser.add_argument('--json', action='store_true',
                            help='Machine-readable output for --list-conflicts.')

    def handle(self, *args, **options):
        if options['audit']:
            return self._audit(options['json'])
        if options['list_conflicts']:
            return self._list_conflicts(options['json'])
        if options['fix_rounding_drift']:
            return self._fix_rounding_drift(options['dry_run'])
        return self._normalize(options)

    def _list_conflicts(self, as_json):
        conflicts = find_conflicts()
        if as_json:
            self.stdout.write(json.dumps(conflicts, indent=2))
            return
        if not conflicts:
            self.stdout.write(self.style.SUCCESS(
                'No product name has conflicting nutrition values.'))
            return
        self.stdout.write(
            f'{len(conflicts)} product name(s) logged with conflicting nutrition:\n')
        for entry in conflicts:
            self.stdout.write(
                f"{entry['product_name']}  ({entry['total_rows']} rows, "
                f"{len(entry['variants'])} variants)")
            for v in entry['variants']:
                self.stdout.write(
                    f"    {v['rows']:>5} rows | {v['calories']} kcal | "
                    f"P {v['protein']}g | F {v['fat']}g | C {v['carbohydrates']}g")

    def _decimal(self, options, key, label):
        raw = options[key]
        if raw is None:
            raise CommandError(f'--{label} is required when using --name.')
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError):
            raise CommandError(f'--{label} must be a number, got {raw!r}.')

    def _normalize(self, options):
        name = options['name']
        if not name:
            raise CommandError('Provide --name (or use --list-conflicts).')

        values = {
            'calories': self._decimal(options, 'calories', 'calories'),
            'protein': self._decimal(options, 'protein', 'protein'),
            'fat': self._decimal(options, 'fat', 'fat'),
            'carbohydrates': self._decimal(options, 'carbs', 'carbs'),
        }

        rows = FoodItem.objects.filter(product_name=name)
        count = rows.count()
        if not count:
            raise CommandError(f'No food entries named {name!r}.')

        before = defaultdict(int)
        for item in rows.only(*NUTRITION_FIELDS):
            before[_profile(item)] += 1

        self.stdout.write(f'{name}: {count} row(s) across {len(before)} variant(s)')
        for profile, n in sorted(before.items(), key=lambda kv: kv[1], reverse=True):
            cal, prot, fat, carb = profile
            self.stdout.write(
                f'    {n:>5} rows | {cal} kcal | P {prot}g | F {fat}g | C {carb}g')
        self.stdout.write(
            f"  -> {values['calories']} kcal | P {values['protein']}g | "
            f"F {values['fat']}g | C {values['carbohydrates']}g")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(
                f'Dry run: {count} row(s) would be updated, none written.'))
            return

        with transaction.atomic():
            updated = rows.update(**values)
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} row(s).'))

    def _fix_rounding_drift(self, dry_run):
        variants = defaultdict(lambda: defaultdict(int))
        for item in FoodItem.objects.all().only('product_name', *NUTRITION_FIELDS):
            variants[item.product_name][_profile(item)] += 1

        repaired = rows_touched = 0
        unresolved = []
        for name, profiles in sorted(variants.items()):
            if len(profiles) < 2:
                continue
            if not _is_rounding_drift(list(profiles)):
                unresolved.append((name, profiles))
                continue

            target = _most_precise(profiles)
            values = dict(zip(NUTRITION_FIELDS, target))
            affected = sum(n for p, n in profiles.items() if p != target)
            self.stdout.write(
                f'{name}: {len(profiles)} rounding variants -> '
                f"{values['calories']} kcal | P {values['protein']}g | "
                f"F {values['fat']}g | C {values['carbohydrates']}g "
                f'({affected} row(s))')
            repaired += 1
            rows_touched += affected
            if not dry_run:
                with transaction.atomic():
                    FoodItem.objects.filter(product_name=name).update(**values)

        verb = 'would be repaired' if dry_run else 'repaired'
        self.stdout.write(self.style.SUCCESS(
            f'{repaired} name(s) {verb} ({rows_touched} row(s) realigned).'))

        if unresolved:
            self.stdout.write(self.style.WARNING(
                f'\n{len(unresolved)} name(s) disagree by more than rounding and '
                f'need manual review (use --name to set the correct values):'))
            for name, profiles in unresolved:
                self.stdout.write(f'  {name}')
                for profile, n in sorted(profiles.items(), key=lambda kv: kv[1], reverse=True):
                    cal, prot, fat, carb = profile
                    self.stdout.write(
                        f'      {n:>5} rows | {cal} kcal | P {prot}g | F {fat}g | C {carb}g')

    def _audit(self, as_json):
        findings = audit_nutrition()
        if as_json:
            self.stdout.write(json.dumps(findings, indent=2))
            return

        headings = (
            ('impossible', 'Physically impossible (a macro outweighs the whole food)'),
            ('density', 'Impossible energy density'),
            ('atwater', 'Macros disagree with stated calories'),
        )
        total = sum(len(findings[key]) for key, _ in headings)
        if not total:
            self.stdout.write(self.style.SUCCESS(
                'No implausible nutrition values found.'))
            return

        for key, heading in headings:
            entries = findings[key]
            if not entries:
                continue
            self.stdout.write(f'\n{heading}: {len(entries)}')
            for name, rows, why in sorted(entries, key=lambda e: -e[1]):
                self.stdout.write(f'  [{rows:>3} rows] {name}')
                self.stdout.write(f'              {why}')

        self.stdout.write(self.style.WARNING(
            f'\n{total} finding(s). Amino-acid supplements legitimately carry '
            f'calories without labelled macros, so review before changing anything.'))
