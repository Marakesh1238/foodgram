import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает данные из JSON файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Путь к JSON файлу')

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']

        with open(json_file, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                for item in data:
                    if 'name' in item and 'measurement_unit' in item:
                        self.stdout.write(
                            self.style.SUCCESS(
                                (
                                    f'Загружаю: {item["name"]} '
                                    f'({item["measurement_unit"]})'
                                )
                            )
                        )
                        Ingredient.objects.get_or_create(
                            name=item['name'],
                            measurement_unit=item['measurement_unit']
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                'Пропущен элемент: Формат неверный'))
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR(
                    'Ошибка при декодировании JSON. Проверьте формат файла.'))

        self.stdout.write(self.style.SUCCESS('Данные успешно загружены.'))
