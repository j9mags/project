from django.core.exceptions import *
from django.views import View
from django.http.response import Http404
from django.shortcuts import render

from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView

from .forms import SetPasswordForm, ForgotPasswordForm
from integration.models import Account, Contact


class UserLogin(LoginView):

    def get(self, request, *args, **kwargs):
        response = super(UserLogin, self).get(request, *args, **kwargs)
        response.context_data.update(forgot_form=ForgotPasswordForm())

        return response


class UserLogout(LogoutView):
    pass


def get_token_or_raise(tk):
    rc = Account.students.filter(cspassword_token=tk)
    pt = rc and rc[0]
    if not pt:
        rc = Contact.university_staff.filter(cspassword_token=tk)
        pt = rc and rc[0]

    if not pt:
        raise Http404()

    if pt.is_token_expired():
        raise PermissionDenied()

    return pt


class PasswordSet(View):

    template_form = 'registration/set_password.html'
    template_done = 'registration/password_set.html'

    def get(self, request, *args, **kwargs):
        tk = request.GET.get('tk', None)

        if not tk:
            raise SuspiciousOperation()

        pt = get_token_or_raise(tk)
        form = SetPasswordForm(initial={'token': pt.cspassword_token})
        context = {'form': form}

        return render(request, self.template_form, context)

    def post(self, request, *args, **kwargs):
        context = {}

        form = SetPasswordForm(request.POST)

        if form.is_valid():
            pt = get_token_or_raise(form.cleaned_data.get('token'))
            UserModel = get_user_model()
            if UserModel.objects.filter(email=pt.get_user_email()).exists():
                user = UserModel.objects.get(email=pt.get_user_email())
            else:
                user = UserModel(email=pt.get_user_email(), is_active=True)
                pt.recordcreated = True
            user.set_password(form.cleaned_data.get('password1'))
            user.save()
            pt.cspassword_token = None
            pt.cspassword_time = None
            pt.save()

            return render(request, self.template_done, context)

        context.update(form=form)

        return render(request, self.template_form, context)


class PasswordChange(View):

    template_success = 'generic/success.html'
    template_failure = 'generic/failure.html'

    def post(self, request, *args, **kwargs):
        context = {}

        form = ForgotPasswordForm(request.POST)

        if (form.is_valid()):
            UserModel = get_user_model()
            qs = UserModel.objects.filter(email=form.cleaned_data.get('email'))

            if qs.exists():
                user = qs.first()
                pt = user.get_srecord()
                pt.request_new_password()

            return render(request, self.template_success, context)

        return render(request, self.template_failure, context)
