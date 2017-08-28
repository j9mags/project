from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language, activate
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.conf import settings

from django.core.exceptions import *
from django.views.generic.base import View
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect

from django.shortcuts import render

from .models import Account
from .forms import StudentOnboardingForm
from .forms import LanguageSelectForm


class StudentMixin(LoginRequiredMixin):

    def get_queryset(self):
        return Account.students.get(
            unimailadresse=self.request.user.email)

    def dispatch(self, request, *args, **kwargs):
        rc = super(StudentMixin, self).dispatch(request, *args, **kwargs)

        lang = get_language()
        account = self.get_queryset()

        if account.kommunikationssprache and not account.kommunikationssprache.startswith(lang):
            user_lang = account.kommunikationssprache[:2]
            activate(user_lang)
            request.session[LANGUAGE_SESSION_KEY] = user_lang
            rc.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_lang)

        return rc


class Dashboard(StudentMixin, TemplateView):
    template_name = 'students/dashboard.html'
    title = 'Student dashboard'

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)

        account = Account.students.get(
            unimailadresse=self.request.user.email)
        contact = account.get_master_contact()
        contract = account.get_active_contract()
        invoice = contract.get_current_invoice()

        context['account'] = account
        context['master_contact'] = contact
        context['active_contract'] = contract
        context['current_invoice'] = invoice

        return context

    def get(self, request, *args, **kwargs):
        response = super(Dashboard, self).get(request, *args, **kwargs)

        if not response.context_data.get('account').initial_review_completed_auto:
            return HttpResponseRedirect('/onboarding/')

        if not response.context_data.get('master_contact').sepalastschriftmandat_erteilt:
            return HttpResponseRedirect('/sepa/' + response.context_data.get('master_contact').pk)

        return response


class AccountDetails(StudentMixin, TemplateView):
    template_name = 'students/onboarding.html'


class Onboard(StudentMixin, View):
    template_lang = 'students/onboarding_lang.html'
    template_data = 'students/onboarding_data.html'

    def get_queryset(self):
        return Account.students.get(
            unimailadresse=self.request.user.email)

    def get_context_data(self, **kwargs):
        context = {}

        account = self.get_queryset()

        context['sf_account'] = account
        context['sf_contact'] = account.contact_set.first()
        context['sf_contract'] = account.contract_account_set.first()

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        account = context.get('sf_account')

        if account.initial_review_completed_auto:
            return HttpResponseRedirect('/')

        if account.kommunikationssprache is None:
            form = LanguageSelectForm()
            context.update(form=form)
            return render(request, self.template_lang, context)

        contact = context.get('sf_contact')
        contract = context.get('sf_contract')

        form = StudentOnboardingForm(initial={
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'salutation': contact.salutation,

            'private_email': contact.email,
            'mobile_phone': contact.mobile_phone,
            'home_phone': contact.home_phone,

            'mailing_street': contact.mailing_street,
            'mailing_city': contact.mailing_city,
            'mailing_zip': contact.mailing_postal_code,
            'mailing_country': contact.mailing_country,

            'gender': account.geschlecht,
            'language': account.kommunikationssprache,
            'nationality': account.staatsangehoerigkeit,
            'birth_city': account.geburtsort,
            'birth_country': account.geburtsland,

            'billing_street': account.billing_street,
            'billing_city': account.billing_city,
            'billing_zip': account.billing_postal_code,
            'billing_country': account.billing_country,

            'billing_option': contract.payment_interval,
        })

        context.update(form=form)

        return render(request, self.template_data, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        account = context.get('sf_account')

        if account.kommunikationssprache is None:
            form = LanguageSelectForm(request.POST)
            context.update(form=form)
            if not form.is_valid():
                print('Not valid')
                return render(request, self.template_lang, context)
            account.kommunikationssprache = form.cleaned_data.get('language')

            try:
                account.save()
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template_lang, context)

            return HttpResponseRedirect('/onboarding')

        form = StudentOnboardingForm(request.POST)
        context.update(form=form)

        if not form.is_valid():
            return render(request, self.template_data, context)

        contact = context.get('sf_contact')
        contract = context.get('sf_contract')

        data = form.cleaned_data

        contact.salutation = data.get('salutation')
        contact.first_name = data.get('first_name')
        contact.last_name = data.get('last_name')
        contact.email = data.get('private_email')
        contact.mobile_phone = data.get('mobile_phone')
        contact.home_phone = data.get('home_phone')
        contact.mailing_street = data.get('mailing_street')
        contact.mailing_city = data.get('mailing_city')
        contact.mailing_postal_code = data.get('mailing_zip')
        contact.mailing_country = data.get('mailing_country')

        account.name = '{salutation} {first_name} {last_name}'.format(**data)
        account.geschlecht = data.get('gender')
        account.kommunikationssprache = data.get('language')
        account.staatsangehoerigkeit = data.get('nationality')
        account.geburtsort = data.get('birth_city')
        account.geburtsland = data.get('birth_country')
        account.billing_street = data.get('billing_street')
        account.billing_city = data.get('billing_city')
        account.billing_postal_code = data.get('billing_zip')
        account.billing_country = data.get('billing_country')

        contract.payment_interval = data.get('billing_option')

        try:
            account.save()
            contact.save()
            contract.save()
        except Exception as e:
            form.add_error(None, str(e))
            return render(request, self.template_data, context)

        return HttpResponseRedirect('/sepa/' + contact.pk)


class ContactSEPA(StudentMixin, TemplateView):

    template_name = 'students/contact_sepa.html'

    def get_context_data(self, **kwargs):
        pk = kwargs.get('pk')
        if pk is None:
            raise SuspiciousOperation()

        context = super(ContactSEPA, self).get_context_data(**kwargs)

        account = Account.students.get(
            unimailadresse=self.request.user.email)

        contact = account.contact_set.filter(pk=pk)
        if not contact:
            raise SuspiciousOperation()

        context['contact'] = contact[0]
        return context

    def get(self, *args, **kwargs):
        rc = super(ContactSEPA, self).get(*args, **kwargs)

        if rc.context_data.get('contact').sepalastschriftmandat_erteilt:
            return HttpResponseRedirect('/')

        return rc
