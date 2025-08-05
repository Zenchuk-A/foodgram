import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import (
    Ingredient,
)


class Command(BaseCommand):
    help = 'Import Ingredient data from CSV file to DB'

    def handle(self, *args, **kwargs):
        self.import_ingredients()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))

    def import_ingredients(self):
        file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.csv')
        try:
            with open(file_path, encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                total = len(rows)
                for i, row in enumerate(rows, 1):
                    if len(row) < 2:
                        continue
                    name = row[0].strip()
                    measurement_unit = row[1].strip()
                    if name and measurement_unit:
                        try:
                            Ingredient.objects.update_or_create(
                                name=name,
                                defaults={
                                    'measurement_unit': measurement_unit
                                },
                            )
                            self.print_progress(i, total)
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'\nError in row {i}: {str(e)}'
                                )
                            )
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
