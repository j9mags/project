from django.core.exceptions import *
from django.views import View
from django.http.response import Http404
from django.shortcuts import render

from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView

from .models import PerishableToken
from .forms import SetPasswordForm, ForgotPasswordForm


class UserLogin(LoginView):

    def get(self, request, *args, **kwargs):
        response = super(UserLogin, self).get(request, *args, **kwargs)
        response.context_data.update(forgot_form=ForgotPasswordForm())

        return response


class UserLogout(LogoutView):
    pass


class PasswordSet(View):

    template_form = 'registration/set_password.html'
    template_done = 'registration/password_set.html'

    def get_token_or_raise(self, tk):
        rc = PerishableToken.objects.filter(token=tk)
        pt = rc and rc[0]

        if not pt:
            raise Http404()

        if pt.is_expired():
            raise PermissionDenied()

        return pt

    def get(self, request, *args, **kwargs):
        tk = request.GET.get('tk', None)

        if not tk:
            raise SuspiciousOperation()

        pt = self.get_token_or_raise(tk)
        form = SetPasswordForm(initial={'token': pt.token})
        context = {'form': form}

        return render(request, self.template_form, context)

    def post(self, request, *args, **kwargs):
        context = {}

        form = SetPasswordForm(request.POST)

        if (form.is_valid()):
            pt = self.get_token_or_raise(form.cleaned_data.get('token'))

            pt.user.set_password(form.cleaned_data.get('password1'))
            pt.user.is_active = True
            pt.user.save()

            srecord = pt.user.get_srecord()

            srecord.cspassword_token = None
            srecord.save()

            pt.delete()

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
                pt = user.create_token()

                srecord = user.get_srecord()
                srecord.cspassword_token = pt.token
                srecord.save()

            return render(request, self.template_success, context)

        return render(request, self.template_failure, context)
