from django.core.exceptions import *
from django.views import View
from django.http.response import Http404
from django.shortcuts import render, reverse, redirect
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView

from .forms import SetPasswordForm, ForgotPasswordForm
from integration.models import Account, Contact


class UserLogin(LoginView):

    def get(self, request, *args, **kwargs):
        response = super(UserLogin, self).get(request, *args, **kwargs)
        response.context_data.update(forgot_form=ForgotPasswordForm())

        flip = 'show-front'

        if 'msg' in request.GET.keys():
            code = request.GET.get('msg')
            msg = {
                'pw-ch--success': _("Your request has been successfully processed."),
                'pw-ch--failed': _("Something went wrong with your request."),
                'pw-ch--missing': _("We couldn't find a user with that email."),
            }.get(code, None)
            if msg:
                flip = 'show-left'
                response.context_data.update(message=msg)
        response.context_data.update(cube_flip=flip)
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
            query = UserModel.objects.filter(email=pt.user_email)
            if query.exists():
                user = query
            else:
                user = UserModel(email=pt.user_email, is_active=True)
                pt.recordcreated = True
            user.set_password(form.cleaned_data.get('password1'))
            user.save()
            pt.cspassword_token = None
            pt.cspassword_time = None
            pt.save(update_fields=['cspassword_token', 'cspassword_time'])

            return render(request, self.template_done, context)

        context.update(form=form)

        return render(request, self.template_form, context)


class PasswordChange(View):

    def post(self, request, *args, **kwargs):
        form = ForgotPasswordForm(request.POST)
        rc = reverse('authentication:login')

        if (form.is_valid()):
            UserModel = get_user_model()
            qs = UserModel.objects.filter(email=form.cleaned_data.get('email'))

            if qs.exists():
                user = qs.first()
                pt = user.srecord()
                pt.request_new_password()
                rc += '?msg=pw-ch--success'
            else:
                rc += '?msg=pw-ch--missing'
        else:
            rc += '?msg=pw-ch--failed'

        return redirect(rc)
