from django.utils.translation import ugettext_lazy as _

from django.core.exceptions import *
from django.views.generic import DetailView
from django.views.generic.base import View
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.shortcuts import render, redirect

from .models import DegreeCourse, Contract
from .forms import *

from django.core.paginator import Paginator, EmptyPage

from uuid import uuid4


class StaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_unistaff():
            raise PermissionDenied()

        return super(StaffMixin, self).dispatch(request, *args, **kwargs)

    def get_staff_context(self):
        self.contact = self.request.user.get_srecord()
        return dict(contact=self.contact, st_form=StudentsUploadForm(self.contact.account), cs_form=UploadForm())


class DashboardHome(StaffMixin, TemplateView):
    template_name = 'staff/dashboard_home.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(DashboardHome, self).get_context_data(**kwargs))

        students = Account.students.filter(hochschule_ref=self.contact.account)
        courses = DegreeCourse.objects.filter(university=self.contact.account)

        context.update(students=students, courses=courses)
        return context


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
                         contact.account.get_active_courses().get(
                             pk=course).name))
        else:
            if status:
                status = "" if status == "None" else status
                students = students.filter(status=status)
                filters.append((_('Status'), status))

            if course:
                course = None if course == "None" else course
                if course is not None:
                    students = students.filter(contract_account_set__studiengang_ref__pk=course)
                    filters.append(
                        (_('Course'),
                         students.first().contract_account_set.filter(
                             studiengang_ref__pk=course).first().studiengang_ref.name))

            paginator = Paginator(students, s)
            try:
                students = paginator.page(p)
            except EmptyPage:
                students = paginator.page(paginator.num_pages if p > 1 else 0)

        bulk_form = BulkActionsForm(self.contact.account)
        context.update(students=students, filters=filters, bulk_form=bulk_form)
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        contact = context.get('contact')

        st_form = StudentsUploadForm(contact.account, request.POST, request.FILES)
        cs_form = UploadForm(request.POST, request.FILES)

        if 'course' in request.POST:
            form = st_form
        else:
            form = cs_form

        if form.is_valid():
            csv = form.cleaned_data.get('csv')
            charset = csv.charset or 'utf-8'
            content = ''.join([line.decode(charset) for line in csv])

            upd = request.user.csvupload_set.create(
                course=form.cleaned_data.get('course'),
                uuid=str(uuid4()),
                content=content
            )
            return HttpResponseRedirect('/review/' + upd.uuid)
        else:
            context.update(
                display_st=form == st_form,
                display_cs=form == st_form,
                st_form=st_form,
                cs_form=cs_form)

        return render(request, self.template_name, context)


class DashboardCourses(StaffMixin, TemplateView):
    template_name = 'staff/dashboard_courses.html'

    def get_context_data(self, **kwargs):
        context = self.get_staff_context()
        context.update(super(DashboardCourses, self).get_context_data(**kwargs))
        context.update(can_search=True)

        p = int(self.request.GET.get('p', '1'))
        o = self.request.GET.get('o', '-start_of_studies')
        s = int(self.request.GET.get('s', '10'))

        q = self.request.GET.get('q')

        courses = DegreeCourse.objects.filter(university=self.contact.account).order_by(o)
        if q:
            context.update(q=q)
            courses = courses.filter(Q(name__icontains=q))
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

        return self.get(request, *args, **kwargs)


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
        data = upload.get_data(p)
        context.update(data=data)
        if upload.course:
            context.update(course=DegreeCourse.objects.get(pk=upload.course))
        context.update(prev=p - 1, cur=p, next=p + 1 if upload.has_more_data(p) else False)

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        contact = context.get('contact')

        st_form = StudentsUploadForm(contact.account, request.POST, request.FILES)
        cs_form = UploadForm(request.POST, request.FILES)

        if 'course' in request.POST:
            form = st_form
        else:
            form = cs_form

        if form.is_valid():
            csv = form.cleaned_data.get('csv')
            charset = csv.charset or 'utf-8'
            content = ''.join([line.decode(charset) for line in csv])

            upd = request.user.csvupload_set.create(
                course=form.cleaned_data.get('course'),
                uuid=str(uuid4()),
                content=content
            )
            return redirect('integration:upload_review', uuid=upd.uuid)
        else:
            context.update(
                display_st=form == st_form,
                display_cs=form == st_form,
                st_form=st_form,
                cs_form=cs_form)
        template = request.POST.get('view')
        return render(request, template, context)


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
            upload.process()

        return HttpResponseRedirect('/')


# Todo Display all non-bank data
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
        contract = account.get_active_contract()
        if contract:
            context.update(contract=contract)
            discount = contract.get_discount()
            payload = self.request.POST if 'course' in self.request.POST else {'course': contract.studiengang_ref.pk}
            context.update(ctr_form=StudentContractForm(contract.university_ref, payload))
            if 'course' in self.request.POST:
                context.update(dsc_form=DiscountForm(self.request.POST))
            else:
                context.update(dsc_form=DiscountForm(instance=discount))

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
        elif 'course' in request.POST:
            ctr_form = context.get('ctr_form')
            if ctr_form.is_valid():
                contract = context.get('contract')
                contract.studiengang_ref = DegreeCourse.objects.get(pk=ctr_form.cleaned_data.get('course'))
                contract.save()
            dsc_form = context.get('dsc_form')
            if dsc_form.is_valid():
                dsc_form.save()

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


class BulkActions(StaffMixin, View):
    def post(self, request, *args, **kwargs):
        contact = request.user.get_srecord()
        form = BulkActionsForm(contact.account, request.POST)

        if form.is_valid():
            student_pks = [pk for pk in form.cleaned_data.get('students').split(';') if pk]
            students = Account.objects.filter(pk__in=student_pks)

            new_status = form.cleaned_data.get('status')
            if new_status != '--':
                students.update(status=new_status)

            course_pk = form.cleaned_data.get('course')
            if course_pk != '--':
                contracts_pk = [s.get_active_contract().pk for s in students if s.get_active_contract() is not None]
                contracts = Contract.objects.filter(pk__in=contracts_pk)
                course = contact.account.degreecourse_set.get(pk=course_pk)
                contracts.update(studiengang_ref=course)
                # for contract in contracts:
                #     contract.studiengang_ref = course
                #     contract.save()

        return HttpResponseRedirect('/')
