from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language, activate
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.conf import settings

from django.core.exceptions import *
from django.views.generic.base import View
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import *

from .models import Attachment


class StudentMixin(LoginRequiredMixin):
    def get_queryset(self):
        return self.request.user.get_srecord()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_student():
            raise PermissionDenied()

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
        self.account = self.get_queryset()

        contact = self.account.get_master_contact()
        contract = self.account.get_active_contract()
        invoice = contract.get_current_invoice()

        context['account'] = self.account
        context['master_contact'] = contact
        context['active_contract'] = contract
        context['current_invoice'] = invoice

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if not self.account.initial_review_completed:
            step = 'data'
            if not self.account.kommunikationssprache:
                step = 'lang'
            elif not self.account.student_approved:
                step = 'review'
            return redirect('integration:onboarding', step=step)

        return super(Dashboard, self).get(request, *args, **kwargs)


# Todo: Add BankAccount info on Account view with possibility to set a new mandate
class AccountDetails(StudentMixin, TemplateView):
    template_name = 'students/onboarding.html'


class Onboarding(StudentMixin, View):
    steps = ['lang', 'review', 'data', 'sepa']
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

        context = {'step': step, 'sf_account': self.account, 'sf_contact': self.account.get_master_contact(),
                   'sf_contract': self.account.get_active_contract(), 'ignore_drawer': True, 'stepper': (
                {
                    'title': 'Welcome back! | Wilkommen!',
                    'caption': 'Please choose your preferred language | Bitte wählen Sie Ihre bevorzugte Sprache',
                    'template': 'students/onboarding_lang.html',
                    'action': reverse('integration:onboarding', kwargs={'step': 'lang'}),
                    'submit': 'Continue | Fortsetzen',
                },
                {
                    'title': _('Data Review'),
                    'caption': _('Carefully review the data provided by your university'),
                    'template': 'students/onboarding_review.html',
                    'action': reverse('integration:onboarding', kwargs={'step': 'review'}),
                    'back': 'lang',
                    'submit': _('Continue'),
                },
                {
                    'title': _('Complete your registration!'),
                    'caption': _('Fill the form and log into your Chancen account.'),
                    'template': 'students/onboarding_data.html',
                    'action': reverse('integration:onboarding', kwargs={'step': 'data'}),
                    'back': 'review',
                    'submit': _('Continue'),
                },
                {
                    'title': _('Set up your Bank account'),
                    'caption': _('Configure your payment method now or leave it for later.'),
                    'template': 'students/onboarding_sepa.html',
                    'action': reverse('integration:onboarding', kwargs={'step': 'sepa'}),
                    'back': 'data',
                    'submit': _('Continue'),
                },
            )}

        return self.update_context_for(step, context)

    def _get_lang_context(self, context):
        context.update(form=LanguageSelectForm(initial={'language': self.account.kommunikationssprache}))
        context['stepper'][0].update(is_active=True)
        return context

    def _get_review_context(self, context):
        context.update(form=OnboardingReviewForm(initial={'approved': self.account.student_approved}))
        context['stepper'][1].update(is_active=True)
        return context

    def _get_data_context(self, context):
        account = context.get('sf_account')
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
        context['stepper'][2].update(is_active=True)
        return context

    def _get_sepa_context(self, context):
        context.update(form=LanguageSelectForm())
        context['stepper'][3].update(is_active=True)
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

        if account.initial_review_completed:
            return redirect('integration:dashboard')

        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        step = context.get('step')
        if step == 'lang':
            form = LanguageSelectForm(request.POST)
            context.update(form=form)
            if not form.is_valid():
                return render(request, self.template, context)
            self.account.kommunikationssprache = form.cleaned_data.get('language')
            self.account.recordcreated = True
            try:
                self.account.save()
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template, context)
            return redirect('integration:onboarding', step='review')
        elif step == 'review':
            form = OnboardingReviewForm(request.POST)
            if form.is_valid():
                self.account.student_approved = form.cleaned_data.get('approved', False)
                try:
                    self.account.save()
                except Exception:
                    return render(request, self.template, context)
            else:
                context.update(form=form)
                self.account.student_approved = False
                try:
                    self.account.save()
                except Exception as e:
                    form.errors.add(None, str(e))
                return render(request, self.template, context)

            return redirect('integration:onboarding', step='data')
        elif step == 'data':
            form = StudentOnboardingForm(request.POST)
            context.update(form=form)

            if not form.is_valid():
                return render(request, self.template, context)

            account = context.get('sf_account')
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
                return render(request, self.template, context)

            return redirect('integration:onboarding', step='sepa')
        elif step == 'sepa':
            self.account.initial_review_completed = True

            try:
                self.account.save()
            except Exception as e:
                context.update(error=str(e))  # should we rather launch a 500 ??
                return render(request, self.template, context)

            return redirect('integration:dashboard')


class ContactSEPA(StudentMixin, TemplateView):
    template_name = 'students/contact_sepa.html'

    def get_context_data(self, **kwargs):
        pk = kwargs.get('pk')
        if pk is None:
            raise SuspiciousOperation()

        context = super(ContactSEPA, self).get_context_data(**kwargs)
        account = self.request.user.get_srecord()
        contact = account.contact_set.filter(pk=pk)
        if not contact:
            raise SuspiciousOperation()

        context['contact'] = contact[0]
        return context

    def get(self, *args, **kwargs):
        rc = super(ContactSEPA, self).get(*args, **kwargs)

        if rc.context_data.get('contact').sepalastschriftmandat_erteilt:
            return redirect('integration:dashboard')

        return rc


class DownloadAttachment(StudentMixin, View):
    def get(self, *args, **kwargs):
        att_id = kwargs.get('att_id')
        att = Attachment.objects.get(pk=att_id)
        if not att:
            raise ObjectDoesNotExist()

        response = HttpResponse(content_type=att.content_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(att.name)
        response.write(att.fetch_content())

        return response
