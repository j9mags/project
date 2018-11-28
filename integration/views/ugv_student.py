from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import *
# from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation import get_language, activate, check_for_language
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from django.views.generic.base import View

from integration.views.student import ContactDetails
from ..forms import *
from ..models import Contact, RecordType, Attachment

import base64

_logger = logging.getLogger(__name__)


class UgvStudentMixin(LoginRequiredMixin):
    login_url = '/authentication/login'
    default_lang = 'en'

    def get_queryset(self):
        return self.request.user.srecord

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_ugv_student:
            raise PermissionDenied()

        rc = super(UgvStudentMixin, self).dispatch(request, *args, **kwargs)
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

    def get_student_context(self):
        context = {}
        self.account = self.get_queryset()

        account = self.account
        contact = self.account.master_contact
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


class SetLanguage(UgvStudentMixin, View):
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


class Dashboard(UgvStudentMixin, TemplateView):
    template_name = 'students/dashboard.html'
    title = 'Student dashboard'

    def get_context_data(self, **kwargs):
        context = self.get_student_context()
        context.update(super(Dashboard, self).get_context_data(**kwargs))
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if not self.account.review_completed:
            step = 'sepa'
            return redirect('integration:onboarding', step=step)

        return super(Dashboard, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = StudentRevokeMandateForm(request.POST, instance=context['master_contact'])

        if form.is_valid():
            form.save()
        else:
            context.update(display_dlg=True)
        return render(request, self.template_name, context=context)


class ContactDetails(UgvStudentMixin, TemplateView):
    model = Contact
    template_name = 'students/contact.html'

    def get_context_data(self, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            raise SuspiciousOperation()
        context = super(ContactDetails, self).get_context_data(**kwargs)
        context['ignore_drawer'] = True

        self.account = self.get_queryset()

        if pk != 'new':
            contact = self.account.contact_set.filter(pk=pk)
            if not contact.exists():
                raise ObjectDoesNotExist()

            contact = contact.first()
        else:
            contact = Contact(record_type=RecordType.objects.get(sobject_type='Contact', developer_name='Sofortzahler'),
                              account=self.account)
        if self.request.POST:
            form = StudentContactForm(self.request.POST, instance=contact)
        else:
            form = StudentContactForm(instance=contact)
        context.update(contact=contact, form=form)

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


class PaymentDetails(UgvStudentMixin, TemplateView):
    model = Contact
    template_name = 'students/payment.html'

    def get_context_data(self, **kwargs):
        context = super(PaymentDetails, self).get_context_data(**kwargs)
        context['ignore_drawer'] = True

        self.account = self.get_queryset()

        master_contact = self.account.get_student_contact()
        payment_contact = self.account.payment_contact

        if payment_contact == master_contact or self.account.is_ugv_student:
            context['rvk_form'] = StudentRevokeMandateForm(instance=payment_contact)

        if self.request.POST:
            form = StudentPaymentForm(self.request.POST, instance=self.account)
        else:
            form = StudentPaymentForm(instance=self.account)
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


class Onboarding(UgvStudentMixin, View):
    steps = ['sepa']
    template = 'students/onboarding.html'

    def get_context_data(self, **kwargs):
        step = kwargs.get('step') or self.steps[0]
        if step not in self.steps:
            raise ObjectDoesNotExist()

        self.account = self.get_queryset()

        step = 'sepa'

        context = {'step': step, 'sf_account': self.account, 'sf_contact': self.account.master_contact,
                   'sf_contract': self.account.active_contract, 'ignore_drawer': True,
                   'stepper': (
                       {
                           'title': _('SEPA Mandate'),
                           'caption': _('We require authorisation to debit your bank account.'),
                           'template': 'students/onboarding_sepa.html',
                           'action': reverse('integration:onboarding', kwargs={'step': 'sepa'}),
                           'submit': _('Grant mandate'),
                           'skip_submit': True,
                           'is_active': True
                       },
                   )}

        return self.update_context_for(step, context)

    def _get_sepa_context(self, context):
        context['stepper'][0].update(is_active=True)
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

            response = redirect(reverse('integration:language'))
            response['location'] += '?next=' + reverse('integration:onboarding', kwargs={'step': 'review'})
            return response
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
            account = context.get('sf_account')
            _post = request.POST.copy()
            if account.is_ugv:
                _post.update(private_email=account.person_email)
            form = StudentOnboardingForm(_post)
            context.update(form=form)

            if not form.is_valid():
                return render(request, self.template, context)

            contact = context.get('sf_contact')
            contract = context.get('sf_contract')

            data = form.cleaned_data

            contact.email = data.get('private_email')

            contact.home_phone = data.get('home_phone')
            contact.mailing_street = data.get('mailing_street')
            contact.mailing_citcitizenshipy = data.get('mailing_city')
            contact.mailing_postal_code = data.get('mailing_zip')
            contact.mailing_country = data.get('mailing_country')

            account.geschlecht = data.get('gender')
            account.staatsangehoerigkeit = data.get('nationality')
            account.geburtsort = data.get('birth_city')
            account.geburtsland = data.get('birth_country')
            account.billing_street = data.get('billing_street')
            account.billing_city = data.get('billing_city')
            account.billing_postal_code = data.get('billing_zip')
            account.billing_country = data.get('billing_country')
            # account.initial_review_completed = True

            contract.payment_interval = data.get('billing_option')

            # try:
            account.save()
            contact.save()
            contract.save()
            # except Exception as e:
            #     print(e)
            #     form.add_error(None, str(e))
            #     return render(request, self.template, context)

            return redirect('integration:onboarding', step='sepa')
        elif step == 'sepa':
            return redirect(self.account.get_student_contact().sepamandate_url_auto)


class UploadFile(UgvStudentMixin, View):
    template_name = 'students/dashboard.html'

    def get(self, request, *args, **kwargs):
        return redirect('integration:dashboard')

    def post(self, request, *args, **kwargs):
        context = self.get_student_context()
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data.get('file')
            if file is not None:

                with open(file.temporary_file_path(), "rb") as f:
                    body = base64.b64encode(f.read())

                attachment = Attachment(name=file.name, parent_id=self.account.pk, body=body.decode("utf-8"))
                attachment.save()
                return redirect('integration:dashboard')
        context.update(
            form=form,
            message=_('Upload failed')
        )
        return render(request, self.template_name, context)

