from rest_framework.exceptions import ValidationError

FORBIDDEN_NAMES = 'me'


def forbidden_names_validator(value):
    if value.lower() in FORBIDDEN_NAMES:
        raise ValidationError(f'Нельзя использовать имя {value}')
