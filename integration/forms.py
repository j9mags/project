from django.utils.translation import ugettext_lazy as _
from django import forms

import pandas
from pandas.io import json
import logging

from authentication.models import CsvUpload
from .models import Choices, Contact
from .models import Account
from .models import Rabatt

_logger = logging.getLogger(__name__)

SalutationChoices = [('', '')] + Choices.Salutation
CountryChoices = [('', '')] + Choices.Country
GenderChoices = [('', '')] + Choices.Gender
NationalityChoices = [('', '')] + Choices.Nationality
LanguageChoices = [('', '')] + Choices.Language
BillingChoices = [('', '')] + Choices.Payment

KEEP_CURRENT = _('-- Keep current --')


class UploadForm(forms.Form):
    csv = forms.FileField()

    def clean(self):
        cleaned_data = super(UploadForm, self).clean()
        csv = cleaned_data.get('csv')

        if csv is not None:
            try:
                json_data = pandas.read_excel(csv.temporary_file_path()).to_json()
                data = json.loads(json_data)

                is_course = 'course' not in cleaned_data
                if not CsvUpload.is_valid(data, is_course):
                    self.add_error('csv', _('File content is not correct.'))
                else:
                    cleaned_data.update(raw_data=json_data)
            except Exception as e:
                _logger.error(e)
                self.add_error('csv', _('There is a problem with the file.'))

        return cleaned_data


class StudentsUploadForm(UploadForm):
    def __init__(self, university, *args, **kwargs):
        super(StudentsUploadForm, self).__init__(*args, **kwargs)
        self.fields['course'] = forms.ChoiceField(
            choices=[(o.pk, o.name) for o in university.get_active_courses()]
        )


class LanguageSelectForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['kommunikationssprache']
        widgets = {
            'kommunikationssprache': forms.RadioSelect()
        }

    def __init__(self, *args, **kwargs):
        super(LanguageSelectForm, self).__init__(*args, **kwargs)
        self.fields['kommunikationssprache']._choices = Choices.Language


class OnboardingReviewForm(forms.Form):
    approved = forms.BooleanField(label=_('I accept that the data provided by the university is correct.'))


class StudentOnboardingForm(forms.Form):
    gender = forms.ChoiceField(choices=GenderChoices, label=_('Gender'))
    nationality = forms.ChoiceField(choices=NationalityChoices, label=_('Nationality'))

    birth_city = forms.CharField(max_length=255, label=_('Birth city'))
    birth_country = forms.ChoiceField(choices=CountryChoices, label=_('Birth country'))

    private_email = forms.EmailField(label=_('Private email address'))
    mobile_phone = forms.CharField(max_length=40, label=_('Mobile phone'))
    home_phone = forms.CharField(max_length=40, required=False, label=_('Home phone'))

    mailing_street = forms.CharField(max_length=40, label=_('Street and House number'))
    mailing_city = forms.CharField(max_length=255, label=_('City'))
    mailing_zip = forms.CharField(max_length=20, label=_('Postal code'))
    mailing_country = forms.ChoiceField(choices=CountryChoices, label=_('Country'))


class StudentAccountForm(forms.Form):
    status = forms.ChoiceField(choices=Choices.AccountStatus)


class StudentContractForm(forms.Form):
    def __init__(self, university, *args, **kwargs):
        super(StudentContractForm, self).__init__(*args, **kwargs)
        self.fields['course'] = forms.ChoiceField(
            choices=[(o.pk, o.name) for o in university.get_active_courses()],
            required=False
        )


class StudentContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['email', 'mobile_phone', 'other_phone', 'mailing_street',
                  'mailing_city', 'mailing_postal_code', 'mailing_country']


class StudentPaymentForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['billing_street', 'billing_city', 'billing_postal_code', 'billing_country']


class StudentRevokeMandateForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['cancel_bank_account']
        labels = {
            'cancel_bank_account': _('I do want to revoke this mandate.')
        }


class UniversityForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['semester_fee_new']

    def __init__(self, *args, **kwargs):
        super(UniversityForm, self).__init__(*args, **kwargs)
        self.fields['semester_fee_new'].localize = True
        self.fields['semester_fee_new'].widget.is_localized = True


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Rabatt
        fields = ['contract', 'discount_type', 'discount_tuition_fee', 'discount_semester_fee', 'active',
                  'applicable_months', 'utilization']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['discount_type'].widget.choices[0] = ("", "")
        self.fields['discount_tuition_fee'].localize = True
        self.fields['discount_tuition_fee'].widget.is_localized = True
        self.fields['discount_semester_fee'].localize = True
        self.fields['discount_semester_fee'].widget.is_localized = True

    def clean(self):
        cleaned_data = super(DiscountForm, self).clean()
        discount_type = cleaned_data.get('discount_type')
        if 'discard' in self.data:
            cleaned_data.update(active=False)
        elif discount_type == 'Discount Tuition Fee':
            if not cleaned_data.get('discount_tuition_fee'):
                self.add_error('discount_tuition_fee', forms.ValidationError(_('This field is required.')))
            cleaned_data.update(discount_semester_fee=None)
        elif discount_type == 'Discount Semester Fee':
            if not cleaned_data.get('discount_semester_fee'):
                self.add_error('discount_semester_fee', forms.ValidationError(_('This field is required.')))
            cleaned_data.update(discount_tuition_fee=None)

        return cleaned_data


class BulkActionsForm(forms.Form):
    status = forms.ChoiceField(choices=[('--', KEEP_CURRENT)] + Choices.AccountStatus, required=False)
    students = forms.CharField()

    def __init__(self, university, *args, **kwargs):
        super(BulkActionsForm, self).__init__(*args, **kwargs)
        self.fields['course'] = forms.ChoiceField(
            choices=[('--', KEEP_CURRENT)] + [(o.pk, o.name) for o in university.get_active_courses()],
            required=False
        )
