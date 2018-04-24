from django.utils.translation import ugettext as _
from django.utils.translation import get_language, activate
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.conf import settings
from django.core.exceptions import *
from django.core.paginator import Paginator, EmptyPage
from django.views.generic.base import View
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from ..forms import *
from ..models import Attachment, Contact, RecordType

_logger = logging.getLogger(__name__)


class StudentMixin(LoginRequiredMixin):
    login_url = '/authentication/login'

    def get_queryset(self):
        return self.request.user.srecord

    def dispatch(self, request, *args, **kwargs):
        rc = super(StudentMixin, self).dispatch(request, *args, **kwargs)
        if not 200 <= rc.status_code < 300:
            return rc

        if not request.user.is_student:
            raise PermissionDenied()

        lang = get_language()
        account = self.get_queryset()
        if account.kommunikationssprache and not account.kommunikationssprache.startswith(lang):
            user_lang = account.kommunikationssprache.lower()[:2]
            activate(user_lang)
            request.session[LANGUAGE_SESSION_KEY] = user_lang
            rc.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_lang)

        return rc


class SetLanguage(StudentMixin, View):
    def get(self, request, *args, **kwargs):
        next = request.GET.get('next', '/')
        rc = redirect(next)

        lang = get_language()
        account = self.get_queryset()

        if account.kommunikationssprache and not account.kommunikationssprache.startswith(lang):
            user_lang = account.kommunikationssprache.lower()[:2]
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

        contact = self.account.master_contact
        contract = self.account.active_contract
        invoices = contract.all_invoices

        context['account'] = self.account
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
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if not self.account.initial_review_completed:
            step = 'sepa'
            if not self.account.kommunikationssprache:
                step = 'lang'
            elif not self.account.student_approved:
                step = 'review'
            elif not self.account.geburtsort:
                step = 'data'
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


class ContactDetails(StudentMixin, TemplateView):
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


class PaymentDetails(StudentMixin, TemplateView):
    model = Contact
    template_name = 'students/payment.html'

    def get_context_data(self, **kwargs):
        context = super(PaymentDetails, self).get_context_data(**kwargs)
        context['ignore_drawer'] = True

        self.account = self.get_queryset()

        master_contact = self.account.get_student_contact()
        payment_contact = self.account.payment_contact()

        if master_contact == payment_contact:
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

        context = {'step': step, 'sf_account': self.account, 'sf_contact': self.account.master_contact,
                   'title_centered': True, 'sf_contract': self.account.active_contract, 'ignore_drawer': True,
                   'stepper': (
                       {
                           'title': 'Willkommen! | Welcome! ',
                           'caption': 'Bitte wähle deine bevorzugte Sprache. | Please select your preferred language.',
                           'template': 'students/onboarding_lang.html',
                           'action': reverse('integration:onboarding', kwargs={'step': 'lang'}),
                           'submit': 'Continue | Fortsetzen',
                       },
                       {
                           'title': _('Data Review'),
                           'caption': _(
                               'Your university sent us important data for your profile. Please check it carefully. '
                               'Should you find any discrepancies, please contact your university to correct this.'),
                           'template': 'students/onboarding_review.html',
                           'action': reverse('integration:onboarding', kwargs={'step': 'review'}),
                           'back': 'lang',
                           'submit': _('Continue'),
                       },
                       {
                           'title': _('Data input'),
                           'caption': _('Please complete the missing information.'),
                           'template': 'students/onboarding_data.html',
                           'action': reverse('integration:onboarding', kwargs={'step': 'data'}),
                           'back': 'review',
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
            # 'salutation': contact.salutation,

            'private_email': contact.email,
            'mobile_phone': account.phone if account.is_ugv else contact.mobile_phone,
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

            if account.is_ugv:
                account.phone = data.get('mobile_phone')
            else:
                contact.mobile_phone = data.get('mobile_phone')

            contact.home_phone = data.get('home_phone')
            contact.mailing_street = data.get('mailing_street')
            contact.mailing_city = data.get('mailing_city')
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


class DownloadAttachment(StudentMixin, View):
    def get(self, *args, **kwargs):
        att_id = kwargs.get('att_id')
        att = Attachment.objects.get(pk=att_id)
        if not att:
            raise ObjectDoesNotExist()

        rc = att.fetch_content()

        response = HttpResponse(rc, content_type=att.content_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(att.name)

        return response
