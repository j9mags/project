from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class SetPasswordForm(forms.Form):
    token = forms.CharField(max_length=255)

    password1 = forms.CharField(max_length=255, label=_('Password'), initial="")
    password2 = forms.CharField(max_length=255, label=_('Confirm password'), initial="")

    def validate_password(self, user):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        rc = True

        if password2 and (password1 != password2):
            self.add_error('password2', _('Passwords mismatch'))
            rc = False
        else:
            try:
                validate_password(password1, user=user)
            except ValidationError as e:
                rc = False
                for error in e.error_list:
                    self.add_error('password2', error)

        return rc


class ForgotPasswordForm(forms.Form):

    email = forms.EmailField(label=_('Email address'), initial="")
