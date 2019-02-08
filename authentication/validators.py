from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordValidator:
    def __init__(self, min_length=8, alfa_numeric=True, capitals=True, special=True):
        self.min_length = min_length
        self.alfa_numeric = alfa_numeric
        self.capitals = capitals
        self.special = special

    def validate(self, password, user=None):
        errors = []
        if not any(c.islower() for c in password):
            errors.append(ValidationError(
                _('This password must contain at least one lowercase letter.'),
                code='lowercase_missing'
            ))

        if len(password) < self.min_length:
            errors.append(ValidationError(
                _("This password must contain at least %(min_length)d characters."),
                code='password_too_short',
                params={'min_length': self.min_length},
            ))

        if self.alfa_numeric and not any(c.isdigit() for c in password):
            errors.append(ValidationError(
                _('This password must contain at least one number.'),
                code='number_missing'
            ))

        if self.capitals and not any(c.isupper() for c in password):
            errors.append(ValidationError(
                _('This password must contain at least one capital letter.'),
                code='capital_missing'
            ))

        if self.special and not any(not c.isalnum() for c in password):
            errors.append(ValidationError(
                _('This password must contain at least one special character.'),
                code='special_missing'
            ))

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_length)d characters, combine upercase "
            "and lowercase letters, numbers and special characters."
            % {'min_length': self.min_length}
        )
