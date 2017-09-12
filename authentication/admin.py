from django.utils.translation import ugettext_lazy as _

from django.contrib import admin

from django import forms
from django.contrib.auth import get_user_model
# from django.contrib.auth.forms import PasswordResetForm
from django.utils.crypto import get_random_string

from authtools.admin import UserAdmin as DjUserAdmin
from authtools.forms import UserCreationForm

from .models import PerishableToken, CsvUpload


User = get_user_model()


class TokenInline(admin.TabularInline):
    model = PerishableToken
    extra = 0

    fields = ('token', 'expires_at')


class UserCreationForm(UserCreationForm):
    """
    A UserCreationForm with optional password inputs.
    """

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        # If one field gets autocompleted but not the other, our 'neither
        # password or both password' validation will be triggered.
        self.fields['password1'].widget.attrs['autocomplete'] = 'off'
        self.fields['password2'].widget.attrs['autocomplete'] = 'off'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = super(UserCreationForm, self).clean_password2()
        if bool(password1) ^ bool(password2):
            raise forms.ValidationError(_("Fill out both fields"))
        return password2


class UserAdmin(DjUserAdmin):
    """
    A UserAdmin that sends a password-reset email when creating a new user,
    unless a password was entered.
    """
    add_form = UserCreationForm
    add_fieldsets = (
        (None, {
            'description': (
                _("Enter the new user's name and email address and click save. "
                  "The user will be emailed a link allowing them to login to "
                  "the site and set their password (optionally).")
            ),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    # inlines = [TokenInline]

    def save_model(self, request, obj, form, change):
        if not change and not obj.has_usable_password():
            # Django's PasswordResetForm won't let us reset an unusable
            # password. We set it above super() so we don't have to save twice.
            obj.set_password(get_random_string())
            reset_password = True
        else:
            reset_password = False

        super(UserAdmin, self).save_model(request, obj, form, change)
        if reset_password:
            # TODO: tell SF about it
            pass


admin.site.register(User, UserAdmin)
admin.site.register(CsvUpload)
