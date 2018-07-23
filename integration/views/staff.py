from uuid import uuid4

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import *
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation import get_language, activate, check_for_language
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.base import View

import re

from django.contrib import messages

from ..forms import *
from ..models import DegreeCourse, Contract, RecordType


class StaffMixin(LoginRequiredMixin):
    default_lang = 'de'
    login_url = '/authentication/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_unistaff:
            raise PermissionDenied()

        rc = super(StaffMixin, self).dispatch(request, *args, **kwargs)
        if not 200 <= rc.status_code < 300:
            return rc

        lang = request.session.get(LANGUAGE_SESSION_KEY)

        if lang is None:
            lang = get_language() if check_for_language(lang) else self.default_lang
            activate(lang)
            request.session[LANGUAGE_SESSION_KEY] = lang
            rc.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)

        return rc

    def get_staff_context(self):
        self.contact = self.request.user.srecord
        form = UploadCsvForm()
        return dict(contact=self.contact, st_form=form, ap_form=form, cs_form=form, form=form)


class SetLanguage(StaffMixin, View):
    def get(self, request, *args, **kwargs):
        next = request.GET.get('next', '/')
        rc = redirect(next)

        lang = kwargs.get('language', get_language())
        if not check_for_language(lang):
            lang = self.default_lang

        activate(lang)
        request.session[LANGUAGE_SESSION_KEY] = lang
        rc.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)

        return rc


class DashboardHome(StaffMixin, TemplateView):
    template_name = 'staff/dashboard_home.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(DashboardHome, self).get_context_data(**kwargs))

        courses = DegreeCourse.objects.filter(university=self.contact.account)
        context.update(courses=courses)
        if self.contact.account.is_services_customer:
            students = Account.students.filter(hochschule_ref=self.contact.account)
            context.update(students=students)

        if self.contact.account.is_eg_customer:
            applications = Lead.ugv_students.filter(active_application__hochschule_ref=self.contact.account)
            ugvers = Account.students.filter(hochschule_ref=self.contact.account,
                                             record_type__developer_name='UGVStudents')
            invoices = self.contact.account.get_all_invoices()
            context.update(applications=applications, ugvers=ugvers, invoices=invoices)

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        form = UploadCsvForm(request.POST, request.FILES)

        if form.is_valid():
            json_data = form.cleaned_data.get('raw_data')
            d = json.loads(json_data)
            for key in d.keys():
                d[key].pop('0')
                d[key].pop('1')
                d[key].pop('2')
            upd = request.user.csvupload_set.create(
                upload_type=form.cleaned_data.get('upload_type'),
                uuid=str(uuid4()),
                content=json.dumps(d)
            )
            return redirect('integration:upload_review', uuid=upd.uuid)

        context.update(
            display_st=form.data.get('upload_type') == 'st',
            display_ap=form.data.get('upload_type') == 'ap',
            st_form=form,
            ap_form=form,
            form=form,
        )

        return render(request, self.template_name, context)


class DashboardStudents(StaffMixin, TemplateView):
    template_name = 'staff/dashboard_students.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(DashboardStudents, self).get_context_data(**kwargs))
        context.update(can_search=True)

        p = int(self.request.GET.get('p', '1'))
        o = self.request.GET.get('o', 'pk')
        s = int(self.request.GET.get('s', '10'))
        q = self.request.GET.get('q')

        status = self.request.GET.get('status')
        course = self.request.GET.get('course')

        students = Account.students.filter(hochschule_ref=self.contact.account).order_by(o)
        if q:
            context.update(q=q)
            students = students.filter(
                Q(name__icontains=q) | Q(immatrikulationsnummer=q) | Q(unimailadresse__icontains=q))

        filters = []
        if not students:
            students = []
            if status:
                status = "" if status == "None" else status
                filters.append((_('Status'), status))
            if course:
                course = None if course == "None" else course
                if course is not None:
                    filters.append(
                        (_('Course'),
                         self.contact.account.get_active_courses().get(
                             pk=course).name))
        else:
            if status:
                status = "" if status == "None" else status
                students = students.filter(status=status)
                filters.append((_('Status'), status, 'status'))

            if course:
                course = None if course == "None" else course
                if course is not None:
                    students = students.filter(contract_account_set__studiengang_ref__pk=course)
                    filters.append(
                        (_('Course'),
                         students.first().contract_account_set.filter(
                             studiengang_ref__pk=course).first().studiengang_ref.name,
                         'course'
                         ))

            paginator = Paginator(students, s)
            try:
                students = paginator.page(p)
            except EmptyPage:
                students = paginator.page(paginator.num_pages if p > 1 else 0)

        bulk_form = BulkActionsForm(self.contact.account)
        context.update(students=students, filters=filters, bulk_form=bulk_form)
        return context


class DashboardUGVers(StaffMixin, TemplateView):
    template_name = 'staff/dashboard_ugvers.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(DashboardUGVers, self).get_context_data(**kwargs))
        context.update(can_search=True)

        p = int(self.request.GET.get('p', '1'))
        o = self.request.GET.get('o', 'pk')
        s = int(self.request.GET.get('s', '10'))
        q = self.request.GET.get('q')

        status = self.request.GET.get('status')
        course = self.request.GET.get('course')

        students = Account.students.filter(hochschule_ref=self.contact.account,
                                           record_type__developer_name='UGVStudents').order_by(o)
        if q:
            context.update(q=q)
            students = students.filter(
                Q(name__icontains=q) | Q(immatrikulationsnummer=q) | Q(unimailadresse__icontains=q))

        filters = []
        if not students:
            students = []
            if status:
                status = "" if status == "None" else status
                filters.append((_('Status'), status))
            if course:
                course = None if course == "None" else course
                if course is not None:
                    filters.append(
                        (_('Course'),
                         self.contact.account.get_active_courses().get(
                             pk=course).name))
        else:
            if status:
                status = "" if status == "None" else status
                students = students.filter(status=status)
                filters.append((_('Status'), status, 'status'))

            if course:
                course = None if course == "None" else course
                if course is not None:
                    students = students.filter(contract_account_set__studiengang_ref__pk=course)
                    filters.append(
                        (_('Course'),
                         students.first().contract_account_set.filter(
                             studiengang_ref__pk=course).first().studiengang_ref.name,
                         'course'
                         ))

            paginator = Paginator(students, s)
            try:
                students = paginator.page(p)
            except EmptyPage:
                students = paginator.page(paginator.num_pages if p > 1 else 0)

        bulk_form = BulkActionsForm(self.contact.account)
        context.update(students=students, filters=filters, bulk_form=bulk_form)
        return context


class DashboardCourses(StaffMixin, TemplateView):
    template_name = 'staff/dashboard_courses.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(DashboardCourses, self).get_context_data(**kwargs))
        context.update(can_search=True)

        p = int(self.request.GET.get('p', '1'))
        s = int(self.request.GET.get('s', '10'))

        q = self.request.GET.get('q')

        courses = DegreeCourse.objects.filter(university=self.contact.account).order_by('created_date')
        if q:
            context.update(q=q)
            courses = courses.filter(Q(name_studiengang_auto__icontains=q))
        if not courses:
            courses = []
        else:
            paginator = Paginator(courses, s)

            try:
                courses = paginator.page(p)
            except EmptyPage:
                courses = paginator.page(paginator.num_pages if p > 1 else 0)

        if self.request.POST:
            form = UniversityForm(self.request.POST, instance=self.contact.account)
        else:
            form = UniversityForm(instance=self.contact.account)

        context.update(courses=courses, form=form)
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        form = context.get('form')
        if form.is_valid():
            form.save()
            form.add_error(None, _('Semester fee updated successfully.'))

        return render(request, self.template_name, context=context)


class DashboardUniversity(StaffMixin, TemplateView):
    template_name = 'staff/dashboard_university.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(DashboardUniversity, self).get_context_data(**kwargs))
        context.update(university=self.contact.account)

        if self.request.POST:
            form = UniversityForm(self.request.POST, instance=self.contact.account)
        else:
            form = UniversityForm(instance=self.contact.account)

        context.update(form=form)

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        form = context.get('form')
        if form.is_valid():
            form.save()

        return self.get(request, *args, **kwargs)


class DashboardUGVApplications(StaffMixin, TemplateView):
    template_name = 'staff/dashboard_ugvapplications.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(DashboardUGVApplications, self).get_context_data(**kwargs))
        context.update(can_search=True)

        if not self.contact.account.is_eg_customer:
            raise PermissionDenied()

        p = int(self.request.GET.get('p', '1'))
        o = self.request.GET.get('o')
        s = int(self.request.GET.get('s', '10'))
        q = self.request.GET.get('q')

        university_status = self.request.GET.get('university_status')
        status = self.request.GET.get('status')
        course = self.request.GET.get('course')

        if o:
            context['sort_' + o] = '-' if o[0] != '-' else ''

        # apps = Application.objects.filter(hochschule_ref=self.contact.account, lead_ref__isnull=False)
        leads = Lead.ugv_students.filter(active_application__hochschule_ref=self.contact.account).order_by('-pk')
        if q:
            context.update(q=q)
            leads = leads.filter(Q(name__icontains=q) | Q(email__icontains=q))

        filters = []
        if leads:
            if course:
                course = None if course == "None" else course
                if course is not None:
                    leads = leads.filter(active_application__studiengang_ref__pk=course)
                    filters.append(
                        (_('Course'),
                         leads.first().active_application.studiengang_ref.name,
                         'course'
                         ))
            # lead_ids = [app.lead_ref.pk for app in apps]
            # items = Lead.ugv_students.filter(pk__in=lead_ids).order_by(o)  #
            if university_status:
                university_status = "" if university_status == "None" else university_status
                leads = leads.filter(university_status=university_status)
                filters.append((_('University-Status'), university_status, 'university_status'))
            if status:
                status = "" if status == "None" else status
                leads = leads.filter(status=status)
                filters.append((_('Status'), status, 'status'))

            if o:
                leads = sorted(leads, key=lambda x: (getattr(x, o, 'pk') is None, getattr(x, o, 'pk')),
                               reverse=True if o[0] == '-' else False)

            paginator = Paginator(leads, s)
            try:
                leads = paginator.page(p)
            except EmptyPage:
                leads = paginator.page(paginator.num_pages if p > 1 else 0)
        else:
            leads = []
            if status:
                status = "" if status == "None" else status
                filters.append((_('Status'), status))
            if course:
                course = None if course == "None" else course
                if course is not None:
                    filters.append(
                        (_('Course'),
                         self.contact.account.get_active_courses().get(
                             pk=course).name))

        context.update(items=leads, filters=filters)
        return context


class DashboardInvoices(StaffMixin, TemplateView):
    template_name = 'staff/dashboard_invoices.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(DashboardInvoices, self).get_context_data(**kwargs))

        if not self.contact.account.is_eg_customer:
            raise PermissionDenied()

        p = int(self.request.GET.get('p', '1'))
        # o = self.request.GET.get('o', 'invoice_date')
        s = int(self.request.GET.get('s', '10'))
        # q = self.request.GET.get('q')

        status = self.request.GET.get('status')

        invoices = self.contact.account.get_all_invoices()
        filters = []

        if invoices:
            if status:
                status = "" if status == "None" else status
                invoices = invoices.filter(status=status)
                filters.append((_('Status'), status, 'status'))

            # if q:
            #     context.update(q=q)
            #     invoices = invoices.filter(Q(name__icontains=q) | Q(email__icontains=q))

            paginator = Paginator(invoices, s)
            try:
                invoices = paginator.page(p)
            except EmptyPage:
                invoices = paginator.page(paginator.num_pages if p > 1 else 0)
        else:
            invoices = []
            if status:
                status = "" if status == "None" else status
                filters.append((_('Status'), status))

        context.update(items=invoices, filters=filters)
        return context


class FileUpload(StaffMixin, TemplateView):
    template_name = 'staff/upload_review.html'

    def get_context_data(self, **kwargs):
        uuid = kwargs.get('uuid')
        if uuid is None:
            raise SuspiciousOperation()

        context = self.get_staff_context()
        context.update(super(FileUpload, self).get_context_data(**kwargs))

        if uuid == "new" and self.request.POST:
            return context

        try:
            upload = self.request.user.csvupload_set.get(uuid=uuid)
        except Exception as e:
            raise SuspiciousOperation()

        p = int(self.request.GET.get('p', '1'))
        s = int(self.request.GET.get('s', '20'))

        data = upload.parse_data()
        paginator = Paginator(data, s)

        try:
            data = paginator.page(p)
        except EmptyPage:
            data = paginator.page(paginator.num_pages if p > 1 else 0)
        context.update(data=data)

        # if upload.course:
        #     context.update(course=DegreeCourse.objects.get(pk=upload.course))

        err = self.request.GET.get('err')
        err_msg = {
            '1': _('There seem to be missing values, please review the data thoroughly.')
        }.get(err)

        if err_msg:
            context.update(error=err_msg)
        return context


class FileUploadAction(StaffMixin, View):
    def get(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        action = kwargs.get('action')
        if (uuid is None) or (action is None):
            raise SuspiciousOperation()

        if action not in ('discard', 'confirm'):
            raise SuspiciousOperation()

        try:
            upload = self.request.user.csvupload_set.get(uuid=uuid)
        except Exception as e:
            raise SuspiciousOperation()

        if action == 'discard':
            upload.delete()
        else:
            try:
                upload.process()
            except Exception as e:
                print(e)
                errors = [_('There seem to be wrong values or incorrectly formatted, please review the data thoroughly.')]
                try:
                    #bulk-case
                    if len(e.args) > 1:
                        for error in e.args[0].get('results'):
                            if error.get('statusCode') != 201:
                                error_results = error.get('result')
                                for error_result in error_results:
                                    if error_result.get('errorCode') is not None and error_result.get(
                                            'message') is not None:
                                        if error_result.get('errorCode') == 'INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST':
                                            errors.append(error_result.get('message'))
                                        # elif error_result.get('errorCode') == 'DUPLICATE_VALUE':
                                        #     message = error_result.get('message')
                                        #     matches = regex.match(r'^.*\s([a-zA-Z0-9]{18}|[a-zA-Z0-9]{15})$', message)
                                        #     if matches:
                                        #         duplicate_ids.append(matches.group(1))
                                    else:
                                        errors.append(error)
                    else:
                        errors.append(e.data.get('message'))
                except Exception:
                    errors.append(e)
                rc = reverse('integration:upload_review', kwargs={'uuid': uuid})
                message = '\n'.join(str(x) for x in errors)
                messages.add_message(request, messages.INFO, message)
                return redirect(rc)
        return redirect('integration:dashboard')


class StudentRegister(StaffMixin, TemplateView):
    template_name = 'staff/student_register.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(StudentRegister, self).get_context_data(**kwargs))

        if self.request.POST:
            form = CreateStudentForm(self.contact.account, self.request.POST)
        else:
            form = CreateStudentForm(self.contact.account)
        context.update(form=form)

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = context.get('form')

        if form.is_valid():
            acc_rt = RecordType.objects.get(sobject_type='Account', developer_name='Sofortzahler').id
            ctc_rt = RecordType.objects.get(sobject_type='Contact', developer_name='Sofortzahler').id
            ctr_id = RecordType.objects.get(sobject_type='Contract', developer_name='Sofortzahler').id

            account = Account(
                record_type_id=acc_rt,
                hochschule_ref=self.contact.account,
                immatrikulationsnummer=form.cleaned_data.get('immatrikulationsnummer'),
                unimailadresse=form.cleaned_data.get('unimailadresse'),
                status=form.cleaned_data.get('status'),
                name="{} {}".format(form.cleaned_data.get('first_name'), form.cleaned_data.get('last_name')),
                geburtsdatum=form.cleaned_data.get('geburtsdatum'),
                billing_street=form.cleaned_data.get('street'),
                billing_postal_code=form.cleaned_data.get('zip'),
                billing_city=form.cleaned_data.get('city'),
                billing_country=form.cleaned_data.get('country')
            )
            account.save()

            contact = Contact(
                account=account,
                record_type_id=ctc_rt,
                last_name=form.cleaned_data.get('last_name'),
                first_name=form.cleaned_data.get('first_name'),
                email=form.cleaned_data.get('email'),
                mobile_phone=form.cleaned_data.get('mobile_phone'),
                mailing_street=form.cleaned_data.get('street'),
                mailing_postal_code=form.cleaned_data.get('zip'),
                mailing_city=form.cleaned_data.get('city'),
                mailing_country=form.cleaned_data.get('country'),
                student_contact=True,
            )
            contact.save()

            course = account.hochschule_ref.degreecourse_set.get(pk=form.cleaned_data.get('course'))
            contract = Contract(
                account=account,
                record_type_id=ctr_id,
                university_ref=account.hochschule_ref,
                studiengang_ref=course,
                degree_course_fees_ref=course.active_fees
            )
            contract.save()
            if 'save-new' in request.POST:
                return redirect('integration:student_register')
            return redirect('integration:student_review', pk=account.pk)
        return self.render_to_response(context)


class StudentReview(StaffMixin, DetailView):
    model = Account
    template_name = 'staff/student_review.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(StudentReview, self).get_context_data(**kwargs))

        account = context.get('account')
        if self.contact.account.pk != account.hochschule_ref.pk:
            raise ObjectDoesNotExist()

        payload = self.request.POST if 'status' in self.request.POST else {'status': account.status}
        context.update(acc_form=StudentAccountForm(payload))
        contract = account.active_contract
        if contract:
            context.update(contract=contract)
            payload = self.request.POST if 'contract' in self.request.POST else None
            if payload:
                if payload.get('discount_type') == Choices.DiscountType[1][0]:
                    dsc_form_str = DiscountForm(payload, instance=contract.semester_discount)
                    dsc_form_ttn = DiscountForm(instance=contract.tuition_discount)
                elif payload.get('discount_type') == Choices.DiscountType[0][0]:
                    dsc_form_str = DiscountForm(instance=contract.semester_discount)
                    dsc_form_ttn = DiscountForm(payload, instance=contract.tuition_discount)
                else:
                    dsc_form_str = DiscountForm(instance=contract.semester_discount)
                    dsc_form_ttn = DiscountForm(instance=contract.tuition_discount)
            else:
                dsc_form_str = DiscountForm(instance=contract.semester_discount)
                dsc_form_ttn = DiscountForm(instance=contract.tuition_discount)
            context.update(dsc_form_str=dsc_form_str, dsc_form_ttn=dsc_form_ttn)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_staff_context()
        context.update(self.get_context_data(object=self.object, **kwargs))
        if 'status' in request.POST:
            ctr_form = context.get('acc_form')
            if ctr_form.is_valid():
                account = context.get('account')
                account.status = ctr_form.cleaned_data.get('status')
                account.save()
        elif 'contract' in request.POST:
            if request.POST.get('discount_type') == Choices.DiscountType[1][0]:
                dsc_form = context.get('dsc_form_str')
            elif request.POST.get('discount_type') == Choices.DiscountType[0][0]:
                dsc_form = context.get('dsc_form_ttn')

            if dsc_form.is_valid():
                dsc_form.save()
                contract = context.get('contract')
                context.update(dsc_form_str=DiscountForm(instance=contract.get_semester_discount))
                context.update(dsc_form_ttn=DiscountForm(instance=contract.get_tuition_discount))

        return self.render_to_response(context)


class CourseReview(StaffMixin, DetailView):
    model = DegreeCourse
    template_name = 'staff/course_review.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(CourseReview, self).get_context_data(**kwargs))

        if self.object.university.pk != self.contact.account.pk:
            raise ObjectDoesNotExist()
        context.update(course=self.object)
        return context


class ContractReview(StaffMixin, DetailView):
    model = Contract
    template_name = 'staff/contract_review.html'


class UGVApplicationReview(StaffMixin, DetailView):
    model = Lead
    template_name = 'staff/ugvapplication_review.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(UGVApplicationReview, self).get_context_data(**kwargs))

        lead = context.get('lead')
        application = lead.application

        if application is None:
            raise ObjectDoesNotExist()

        if self.contact.account.pk != application.hochschule_ref.pk:
            raise PermissionDenied()

        payload = self.request.POST if 'university_status' in self.request.POST else None
        context.update(application=application, form=UGVApplicationForm(payload, instance=lead))  # initial={'status': application.lead_ref.university_status}))
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_staff_context()
        context.update(self.get_context_data(object=self.object, **kwargs))

        form = context.get('form')
        if form.is_valid():
            form.save()
            context.update(message=_('UGV Application Status successfully updated.'))
        else:
            context.update(form=form)

        return self.render_to_response(context)


class BulkActions(StaffMixin, View):
    def post(self, request, *args, **kwargs):
        contact = request.user.srecord
        form = BulkActionsForm(contact.account, request.POST)

        if form.is_valid():
            student_pks = [pk for pk in form.cleaned_data.get('students').split(';') if pk]
            students = Account.objects.filter(pk__in=student_pks)

            new_status = form.cleaned_data.get('status')
            if new_status != '--':
                students.update(status=new_status)

        referer = request.META.get('HTTP_REFERER')
        if referer is not None:
            referer = re.sub('^https?:\/\/', '', referer).split('/')
            referer = referer[1]
        else:
            referer = 'students'
        message = _("Students have been successfully updated. It may take a while to see the results.")
        messages.add_message(request, messages.INFO, message)
        return redirect('integration:' + referer)


