from django.core.exceptions import PermissionDenied
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.decorators import login_required

from integration.models import Account
# from authentication.views import ForbiddenView


def dispatch_by_user(student_view, staff_view):
    @login_required(login_url='/auth/login/')
    def get_view(request, **kwargs):
        if request.user.is_student():
            return student_view(request, **kwargs)
        elif request.user.is_unistaff():
            return staff_view(request, **kwargs)
        else:
            raise PermissionDenied()
            # return ForbiddenView.as_view()(request, **kwargs)
    return get_view


class StudentDashboard(LoginRequiredMixin, TemplateView):
    login_url = '/auth/login/'
    template_name = 'students/dashboard.html'

    def get_queryset(self):
        return Account.students.get(
            unimailadresse=self.request.user.email)

    def get_context_data(self, **kwargs):
        context = super(StudentDashboard, self).get_context_data(**kwargs)

        account = self.get_queryset()
        context['dashboard_title'] = 'Student dashboard'
        context['sf_account'] = account
        context['sf_contacts'] = account.contact_set.all()
        context['sf_contracts'] = account.contract_account_set.all()

        return context


class StaffDashboard(LoginRequiredMixin, TemplateView):
    login_url = '/auth/login/'
    template_name = 'staff/dashboard.html'

    def get_queryset(self):
        return Account.universities.get(
            unimailadresse=self.request.user.email)
