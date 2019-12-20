from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import *
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation import get_language, activate, check_for_language
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from django.views.generic.base import View

from salesforce.backend.driver import SalesforceError

from ..forms import *
from ..models import Case, RecordType, ContentVersion, FeedItem, Contact

import base64
import datetime


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
                lang = self.default_lang

            activate(lang)
            request.session[LANGUAGE_SESSION_KEY] = lang
            rc.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)

        return rc

    def get_repayer_context(self):
        context = {}
        self.account = self.get_queryset()

        contracts = self.account.contract_account_set.all()
        cases = self.account.get_open_cases()
        closed_cases = self.account.get_closed_cases()

        translated_sexes = dict(Choices.Biological_Sex)
        translated_nationalities = dict(Choices.Nationality)
        translated_languages = dict(Choices.Language)
        translated_countries = dict(Choices.Country)

        self.account.translated_sex = translated_sexes.get(self.account.master_contact.biological_sex,
                                                           self.account.master_contact.biological_sex)
        self.account.translated_nationality = translated_nationalities.get(self.account.citizenship, self.account.citizenship)
        self.account.translated_shipping_country = translated_countries.get(self.account.shipping_country, self.account.shipping_country)
        self.account.translated_billing_country = translated_countries.get(self.account.billing_country, self.account.billing_country)
        self.account.translated_language = translated_languages.get(self.account.kommunikationssprache,
                                                                    self.account.kommunikationssprache)
        self.account.master_contact.translated_mailing_country = translated_countries.get(self.account.master_contact.mailing_country, 
                                                                                          self.account.master_contact.mailing_country)

        context['account'] = self.account
        context['master_contact'] = self.account.master_contact
        context['contracts'] = contracts
        context['cases'] = cases
        context['closed_cases'] = closed_cases

        clarification_needed = False
        for case in cases:
            if case.status == 'Clarification Needed':
                clarification_needed = True
                break
        context['clarification_needed'] = clarification_needed

        context['ignore_drawer'] = True

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
        elif not self.account.person_mobile_phone:
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
        # contact = context.get('sf_contact')
        # contract = context.get('sf_contract')

        try:
            if not (account.shipping_street or account.shipping_city or
                    account.shipping_postal_code or account.shipping_country):
                account.shipping_street = account.billing_street
                account.shipping_city = account.billing_city
                account.shipping_postal_code = account.billing_postal_code
                account.shipping_country = account.billing_country
            elif not (account.billing_street or account.billing_city or
                      account.billing_postal_code or account.billing_country):
                account.billing_street = account.shiping_street
                account.billing_city = account.shipping_city
                account.billing_postal_code = account.shipping_postal_code
                account.billing_country = account.shipping_country

            form = RepayerOnboardingForm(initial={
                # 'first_name': contact.first_name,
                # 'last_name': contact.last_name,
                # 'salutation': contact.salutation,

                # 'private_email': account.person_email,
                'mobile_phone': account.person_mobile_phone,
                'home_phone': account.phone,

                'shipping_street': account.shipping_street,
                'shipping_city': account.shipping_city,
                'shipping_zip': account.shipping_postal_code,
                'shipping_country': account.shipping_country,

                # 'gender': account.geschlecht,
                'language': account.kommunikationssprache,
                # 'nationality': account.staatsangehoerigkeit,
                # 'birth_city': account.geburtsort,
                # 'birth_country': account.geburtsland,

                'billing_street': account.billing_street,
                'billing_city': account.billing_city,
                'billing_zip': account.billing_postal_code,
                'billing_country': account.billing_country,

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

            # account.person_email = data.get('private_email')
            account.person_mobile_phone = data.get('mobile_phone')
            account.phone = data.get('home_phone')

            account.shipping_street = data.get('shipping_street')
            account.shipping_city = data.get('shipping_city')
            account.shipping_postal_code = data.get('shipping_zip')
            account.shipping_country = data.get('shipping_country')

            account.billing_street = data.get('billing_street')
            account.billing_city = data.get('billing_city')
            account.billing_postal_code = data.get('billing_zip')
            account.billing_country = data.get('billing_country')

            try:
                account.save()
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template, context)

            return redirect('integration:onboarding', step='sepa')
        elif step == 'sepa':
            account = context.get('sf_account')
            account.initial_review_completed = True

            try:
                account.save()
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template, context)

            return redirect(self.account.get_repayer_contact().sepamandate_url_auto)


class Dashboard(RepayerMixin, TemplateView):
    template_name = 'repayer/dashboard.html'
    title = 'Dashboard'

    def get_context_data(self, **kwargs):
        context = self.get_repayer_context()
        context.update(super(Dashboard, self).get_context_data(**kwargs))

        panel = self.request.GET.get('v')
        if panel not in ('account', 'contracts', 'support'):
            panel = 'account'
        context.update(panel=panel)

        return context

    def get(self, request, *args, **kwargs):
        self.get_context_data(**kwargs)

        if not self.account.review_completed:
            step = 'sepa'
            if not self.account.kommunikationssprache:
                step = 'lang'
            elif not self.account.person_mobile_phone:
                step = 'data'
            return redirect('integration:onboarding', step=step)

        return super(Dashboard, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = RuckRevokeMandateForm(request.POST, instance=self.account)

        if form.is_valid():
            form.save()
        else:
            context.update(display_dlg=True)
        return render(request, self.template_name, context=context)

class ContactDetails(RepayerMixin, TemplateView):
    model = Contact
    template_name = 'repayer/contact.html'

    def get_context_data(self, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            raise SuspiciousOperation()
        
        context = super(ContactDetails, self).get_context_data(**kwargs)
        context['ignore_drawer'] = True

        self.account = self.get_queryset()

        if self.request.POST:
            form = PersonContactForm(self.request.POST, instance=self.account)
        else:
            form = PersonContactForm(instance=self.account)
        
        context.update(form=form, account=self.account)

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        form = context.get('form')
        if form.is_valid():
            try:
                form.save()
                return redirect('integration:dashboard')
            except Exception as e:
                form.add_error(None, str(e))
        return render(request, self.template_name, context)

class PaymentDetails(RepayerMixin, TemplateView):
    model = Contact
    template_name = 'repayer/payment.html'

    def get_context_data(self, **kwargs):
        context = self.get_repayer_context()
        context.update(super(PaymentDetails, self).get_context_data(**kwargs))
        context['ignore_drawer'] = True

        payment_contact = context['master_contact']

        context['rvk_form'] = RuckRevokeMandateForm(instance=self.account)

        if self.request.POST:
            form = PaymentForm(self.request.POST, instance=self.account)
        else:
            form = PaymentForm(instance=self.account)
        context.update(account=self.account, form=form)

        if payment_contact:
            context.update(open_payments=payment_contact.mandate_open_payments or 0)
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if 'cancel_bank_account' in request.POST:
            context.update(display_dlg=True)
            form = context.get('rvk_form')
        else:
            form = context.get('form')

        if form.is_valid():
            try:
                form.save()
                return redirect('integration:dashboard')
            except Exception as e:
                form.add_error(None, str(e))

        return render(request, self.template_name, context)


class NewRequest(RepayerMixin, TemplateView):
    template_name = 'repayer/request.html'
    title = 'New Request'

    def get_context_data(self, **kwargs):
        context = self.get_repayer_context()
        context.update(super(NewRequest, self).get_context_data(**kwargs))

        pk = kwargs.get('pk')
        if (pk is not None):
            case = Case.objects.get(pk=pk)
            if case.is_locked:
                return reverse('integration:dashboard') + '?v=support'
        else:
            case = Case(record_type=RecordType.objects.get(sobject_type='Case', developer_name='Ruckzahler'),
                        account=self.account, contact=self.account.master_contact)
        
        ruckzahler = [x for x in context.get('contracts', []) if x.is_ruckzahler]
        ruckzahler = ruckzahler and ruckzahler[0]
        context.update(relevant_income=ruckzahler.annual_minimal_income_indexed, gross_income=ruckzahler.gross_income)

        if self.request.POST:
            data = self.request.POST.copy()
            
            if data['effective_start_trig']:
                data['effective_start_trig'] = datetime.date(*(int(x) for x in data['effective_start_trig'].split('-')))
            if data['effective_end']:
                data['effective_end'] = datetime.date(*(int(x) for x in data['effective_end'].split('-')))
            
            form = RepayerCaseForm(data, self.request.FILES, instance=case)
        else:
            initial = {
                'subject': case.subject or '',
                'type': case.type or '',
                'effective_start_trig': case.effective_start_trig or '',
                'effective_end': case.effective_end or '',
                'relevant_income_trig': case.relevant_income_trig or '',
                'description': case.description or '',
            }
            form = RepayerCaseForm(instance=case, initial=initial)
        context.update(case=case, form=form)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if context == reverse('integration:dashboard'):
            return redirect(context)

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if context == reverse('integration:dashboard') + '?v=support':
            return redirect(context)

        form = context.get('form')
        if form.is_valid():
            try:
                form.save()
            except SalesforceError as e:
                data = e.response.json()[0]
                field = data.get('fields')
                field = field and field[0].lower()
                field = field if field in form.fields else None

                form.add_error(field, (data.get('message')))
                return render(request, self.template_name, context)
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template_name, context)

            case = form.instance
            cvv = []
            for f in self.request.FILES.getlist('evidence'):
                cv = ContentVersion(path_on_client=f.name, version_data=base64.b64encode(f.read()).decode('UTF-8'),
                                    title=f.name)
                try:
                    cv.save()
                except Exception as e:
                    case.delete()
                    form.add_error(None, str(e.message))
                    return render(request, self.template_name, context)
                cvv.append(cv)

            for cv in cvv:
                fi = FeedItem(parent=case, related_record=cv)
                try:
                    fi.save()
                except Exception as e:
                    case.delete()
                    form.add_error(None, str(e.message))
                    return render(request, self.template_name, context)

            return redirect(reverse('integration:dashboard') + '?v=support')

        return render(request, self.template_name, context)
