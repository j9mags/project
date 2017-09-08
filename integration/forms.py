from django.utils.translation import ugettext_lazy as _
from django import forms

from .models import Choices
from .models import Account
from .models import Rabatt


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
            ctype = csv.content_type
            charset = csv.charset or 'utf-8'
            if not ctype.startswith('text/'):
                self.add_error('csv', "File doesn't seem to be a valid CSV")

            headers = None
            first_line = None

            for line in csv:
                if headers is None:
                    headers = line.decode(charset)
                elif first_line is None:
                    first_line = line.decode(charset)
                else:
                    break

            if not headers or not first_line:
                self.add_error('csv', "File doesn't seem to be a valid CSV")

        return cleaned_data


class StudentsUploadForm(UploadForm):
    def __init__(self, university, *args, **kwargs):
        super(StudentsUploadForm, self).__init__(*args, **kwargs)
        self.fields['course'] = forms.ChoiceField(
            choices=[(o.pk, o.name) for o in university.get_active_courses()]
        )


class LanguageSelectForm(forms.Form):
    language = forms.ChoiceField(choices=Choices.Language, widget=forms.RadioSelect)


class OnboardingReviewForm(forms.Form):
    approved = forms.BooleanField()


class StudentOnboardingForm(forms.Form):
    salutation = forms.ChoiceField(choices=SalutationChoices, required=False)
    first_name = forms.CharField(max_length=40)
    last_name = forms.CharField(max_length=80)

    gender = forms.ChoiceField(choices=GenderChoices)
    nationality = forms.ChoiceField(choices=NationalityChoices)
    language = forms.ChoiceField(choices=LanguageChoices)

    birth_city = forms.CharField(max_length=255)
    birth_country = forms.ChoiceField(choices=CountryChoices)

    private_email = forms.EmailField()
    mobile_phone = forms.CharField(max_length=40)
    home_phone = forms.CharField(max_length=40, required=False)

    mailing_street = forms.CharField(max_length=40, label=_('Street address'))
    mailing_city = forms.CharField(max_length=255, label=_('City'))
    mailing_zip = forms.CharField(max_length=20, label=_('Postal code'))
    mailing_country = forms.ChoiceField(choices=CountryChoices, label=_('Country'))

    billing_street = forms.CharField(max_length=40, label=_('Street address'))
    billing_city = forms.CharField(max_length=255, label=_('City'))
    billing_zip = forms.CharField(max_length=20, label=_('Postal code'))
    billing_country = forms.ChoiceField(choices=CountryChoices, label=_('Country'))

    billing_option = forms.ChoiceField(choices=BillingChoices)  # Todo: note to student it's only settable once


class StudentAccountForm(forms.Form):
    status = forms.ChoiceField(choices=Choices.AccountStatus)


class StudentContractForm(forms.Form):
    def __init__(self, university, *args, **kwargs):
        super(StudentContractForm, self).__init__(*args, **kwargs)
        self.fields['course'] = forms.ChoiceField(
            choices=[(o.pk, o.name) for o in university.get_active_courses()],
            required=False
        )


class UniversityForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['semester_fee_new']


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Rabatt
        fields = ['contract', 'discount_type', 'discount_tuition_fee', 'discount_semester_fee']


class BulkActionsForm(forms.Form):
    status = forms.ChoiceField(choices=[('--', KEEP_CURRENT)] + Choices.AccountStatus, required=False)
    students = forms.CharField()

    def __init__(self, university, *args, **kwargs):
        super(BulkActionsForm, self).__init__(*args, **kwargs)
        self.fields['course'] = forms.ChoiceField(
            choices=[('--', KEEP_CURRENT)] + [(o.pk, o.name) for o in university.get_active_courses()],
            required=False
        )
