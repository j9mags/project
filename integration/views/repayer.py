from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import *
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation import get_language, activate, check_for_language
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from django.views.generic.base import View


from ..forms import *
from ..models import Attachment

import base64

_logger = logging.getLogger(__name__)


class RepayerMixin(LoginRequiredMixin):
    login_url = '/authentication/login'
    default_lang = 'en'

    def get_queryset(self):
        return self.request.user.srecord

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_repayer:
            raise PermissionDenied()

        rc = super(RepayerMixin, self).dispatch(request, *args, **kwargs)
        if not 200 <= rc.status_code < 300:
            return rc

        lang = request.session.get(LANGUAGE_SESSION_KEY)

        if lang is None:
            account = self.get_queryset()

            try:
                language_code = dict(Choices.LanguageCode).get(account.kommunikationssprache).lower()
                lang = language_code if language_code is not None else get_language()
                lang = lang if check_for_language(lang) else self.default_lang
            except Exception as e:
                print(e)
                lang = self.default_lang

            activate(lang)
            request.session[LANGUAGE_SESSION_KEY] = lang
            rc.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)

        return rc

    def get_repayer_context(self):
        context = {}
        self.account = self.get_queryset()

        account = self.account
        # contact = self.account.master_contact
        contract = self.account.active_contract
        invoices = contract.all_invoices if contract is not None else None
        uploaded_files = Attachment.objects.filter(parent_id=self.account.pk)

        translated_sexes = dict(Choices.Biological_Sex)
        translated_nationalities = dict(Choices.Nationality)
        translated_languages = dict(Choices.Language)
        translated_countries = dict(Choices.Country)

        account.translated_sex = translated_sexes.get(account.master_contact.biological_sex, account.master_contact.biological_sex)
        account.translated_nationality = translated_nationalities.get(account.citizenship, account.citizenship)
        account.translated_language = translated_languages.get(account.kommunikationssprache, account.kommunikationssprache)
        contact.translated_mailing_country = translated_countries.get(contact.mailing_country, contact.mailing_country)

        context['account'] = account
        context['master_contact'] = contact
        context['payment_contact'] = self.account.payment_contact
        context['active_contract'] = contract
        context['ignore_drawer'] = True

        p = int(self.request.GET.get('p', '1'))
        s = int(self.request.GET.get('s', '10'))

        if invoices:
            paginator = Paginator(invoices, s)
            try:
                invoices = paginator.page(p)
            except EmptyPage:
                invoices = paginator.page(paginator.num_pages if p > 1 else 0)

        context['invoices'] = invoices
        context['uploaded_files'] = uploaded_files
        return context


class SetLanguage(RepayerMixin, View):
    def get(self, request, *args, **kwargs):
        next = request.GET.get('next', '/')
        rc = redirect(next)

        lang = kwargs.get('language')
        account = self.get_queryset()

        if not check_for_language(lang):
            lang = account.kommunikationssprache.lower()[:2] \
                if account.kommunikationssprache is not None else get_language()

        if not check_for_language(lang):
            lang = self.default_lang

        activate(lang)
        request.session[LANGUAGE_SESSION_KEY] = lang
        rc.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)

        return rc


class Onboarding(RepayerMixin, View):
    steps = ['lang', 'data', 'sepa']
    template = 'students/onboarding.html'

    def get_context_data(self, **kwargs):
        step = kwargs.get('step') or self.steps[0]
        if step not in self.steps:
            raise ObjectDoesNotExist()

        self.account = self.get_queryset()

        if not self.account.kommunikationssprache:
            step = 'lang'
        elif not self.account.student_approved:
            if step not in self.steps[:1]:
                step = 'review'
        elif not self.account.geburtsort:
            if step not in self.steps[:2]:
                step = 'data'

        context = {'step': step, 'sf_account': self.account, 'sf_contact': self.account.master_contact,
                   'sf_contract': self.account.active_contract, 'ignore_drawer': True,
                   'stepper': (
                       {
                           'title': 'Willkommen! | Welcome! ',
                           'caption': 'Bitte wähle deine bevorzugte Sprache. | Please select your preferred language.',
                           'template': 'students/onboarding_lang.html',
                           'action': reverse('integration:onboarding', kwargs={'step': 'lang'}),
                           'submit': 'Continue | Fortsetzen',
                       },
                       {
                           'title': _('Data input'),
                           'caption': _('Please complete the missing information.'),
                           'template': 'repayer/onboarding_data.html',
                           'action': reverse('integration:onboarding', kwargs={'step': 'data'}),
                           'back': 'lang',
                           'submit': _('Continue'),
                       },
                       {
                           'title': _('SEPA Mandate'),
                           'caption': _('We require authorisation to debit a bank account for your tuition fees.'),
                           'template': 'students/onboarding_sepa.html',
                           'action': reverse('integration:onboarding', kwargs={'step': 'sepa'}),
                           'back': 'data',
                           'submit': _('Grant mandate'),
                           'skip_submit': True
                       },
                   )}

        return self.update_context_for(step, context)

    def _get_lang_context(self, context):
        if self.request.POST:
            form = LanguageSelectForm(self.request.POST, instance=self.account)
        else:
            form = LanguageSelectForm(instance=self.account)

        context.update(form=form)
        context['stepper'][0].update(is_active=True)
        return context

    def _get_data_context(self, context):
        account = context.get('sf_account')
        contact = context.get('sf_contact')
        contract = context.get('sf_contract')

        try:
            form = RepayerOnboardingForm(initial={
                # 'first_name': contact.first_name,
                # 'last_name': contact.last_name,
                # 'salutation': contact.salutation,

                'private_email': account.person_email,
                'mobile_phone': account.person_mobile_phone,
                'home_phone': account.phone,

                'mailing_street': account.person_mailing_street,
                'mailing_city': account.person_mailing_city,
                'mailing_zip': account.person_mailing_postal_code,
                'mailing_country': account.person_mailing_country,

                # 'gender': account.geschlecht,
                'language': account.kommunikationssprache,
                # 'nationality': account.staatsangehoerigkeit,
                # 'birth_city': account.geburtsort,
                # 'birth_country': account.geburtsland,

                # 'billing_street': account.billing_street,
                # 'billing_city': account.billing_city,
                # 'billing_zip': account.billing_postal_code,
                # 'billing_country': account.billing_country,

                # 'billing_option': contract.payment_interval if contract else None
            })
        except AttributeError:
            form = RepayerOnboardingForm()

        context.update(form=form)
        context['stepper'][1].update(is_active=True)
        return context

    def _get_sepa_context(self, context):
        context['stepper'][2].update(is_active=True)
        return context

    def update_context_for(self, step, context):
        try:
            get = self.__getattribute__('_get_{}_context'.format(step))
            context = get(context)
        except AttributeError:
            pass
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        account = context.get('sf_account')

        if account.review_completed:
            return redirect('integration:dashboard')

        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        step = context.get('step')
        languages = {'German': 'de', 'English': 'en'}
        if step == 'lang':
            form = context.get('form')
            if not form.is_valid():
                return render(request, self.template, context)
            try:
                form.save()
            except Exception as e:
                print(e)
                form.add_error(None, str(e))
                return render(request, self.template, context)
            lang = languages.get(form.cleaned_data.get('kommunikationssprache'), 'en')
            response = redirect(reverse('integration:setlanguage', kwargs={'language': lang}))
            response['location'] += '?next=' + reverse('integration:onboarding', kwargs={'step': 'data'})
            return response
        elif step == 'data':
            account = context.get('sf_account')
            _post = request.POST.copy()
            form = RepayerOnboardingForm(_post)
            context.update(form=form)

            if not form.is_valid():
                return render(request, self.template, context)

            # contact = context.get('sf_contact')
            # contract = context.get('sf_contract')

            data = form.cleaned_data

            account.person_email = data.get('private_email')

            account.person_mobile_phone = data.get('mobile_phone')

            account.phone = data.get('home_phone')
            account.person_mailing_street = data.get('mailing_street')
            account.person_mailing_city = data.get('mailing_city')
            account.person_mailing_postal_code = data.get('mailing_zip')
            account.person_mailing_country = data.get('mailing_country')

            try:
                account.save()
            except Exception as e:
                print(e)
                form.add_error(None, str(e))
                return render(request, self.template, context)

            return redirect('integration:onboarding', step='sepa')
        elif step == 'sepa':
            return redirect(self.account.get_repayer_contact().sepamandate_url_auto)
