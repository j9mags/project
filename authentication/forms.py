from django.utils.translation import ugettext_lazy as _
from django import forms


class SetPasswordForm(forms.Form):
    token = forms.CharField(max_length=255)

    password1 = forms.CharField(max_length=255, label=_('Password'), initial="")
    password2 = forms.CharField(max_length=255, label=_('Confirm password'), initial="")

    def clean(self):
        cleaned_data = super(SetPasswordForm, self).clean()

        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password2 and (password1 != password2):
            self.add_error('password2', _('Passwords mismatch'))

        return cleaned_data


class ForgotPasswordForm(forms.Form):

    email = forms.EmailField(label=_('Email address'), initial="")
