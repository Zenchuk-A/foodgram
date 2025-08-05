import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import ingredients from JSON file'

    def handle(self, *args, **kwargs):
        self.import_ingredients()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))

    def import_ingredients(self):
        file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
                total = len(data)
                for i, item in enumerate(data, 1):
                    try:
                        Ingredient.objects.update_or_create(
                            name=item['name'].strip(),
                            defaults={
                                'measurement_unit': item[
                                    'measurement_unit'
                                ].strip()
                            },
                        )
                        self.print_progress(i, total)
                    except KeyError as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'\nMissing required field: {str(e)} '
                                f'in item {i}'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'\nError processing item {i}: {str(e)}'
                            )
                        )
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('\nInvalid JSON format'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nError reading file: {str(e)}')
            )

    def print_progress(self, current, total):
        progress = int(100 * current / total)
        self.stdout.write(
            f'\rProcessing: {current}/{total} ({progress}%)',
            ending='\r' if current < total else '\n',
        )
        self.stdout.flush()
