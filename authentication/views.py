from django.core.exceptions import *
from django.views import View
#  from django.http.response import Http404
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
                'pw-ch--missing': _("We couldn't find a user with that email. Please contact info@chancen-eg.de if you "
                                    "are sure that you used this email address to sign up for the CHANCEN Portal."),
                'expired': _("This url is no longer valid. Please contact info@chancen-eg.de for further information."),
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
        rc = Account.ugv_students.filter(cspassword_token=tk)
        pt = rc and rc[0]
    if not pt:
        rc = Account.repayers.filter(csspassword_token=tk)
        pt = rc and rc[0]
    if not pt:
        rc = Contact.university_staff.filter(cspassword_token=tk)
        pt = rc and rc[0]

    if not pt:
        return False  # raise Http404()

    if pt.is_token_expired():
        return False  # raise PermissionDenied()

    return pt


class PasswordSet(View):

    template_form = 'registration/set_password.html'
    template_done = 'registration/password_set.html'

    def get(self, request, *args, **kwargs):
        tk = request.GET.get('tk', None)

        if not tk:
            raise SuspiciousOperation()

        pt = get_token_or_raise(tk)
        if not pt:
            return redirect(reverse('authentication:login') + '?msg=expired')

        form = SetPasswordForm(initial={'token': pt.cs_token})
        context = {'form': form}

        return render(request, self.template_form, context)

    def post(self, request, *args, **kwargs):
        context = {}

        form = SetPasswordForm(request.POST)
        if form.is_valid():
            tk = form.cleaned_data.get('token')
            pt = get_token_or_raise(tk)
            UserModel = get_user_model()
            query = UserModel.objects.filter(email=pt.user_email)
            if query.exists():
                user = query.first()
            else:
                user = UserModel(email=pt.user_email, is_active=True)
                pt.recordcreated = True

            if not form.validate_password(user):
                context.update(form=form)
                return render(request, self.template_form, context)

            user.set_password(form.cleaned_data.get('password1'))
            user.save()

            pt.clear_token()
            pt.save(update_fields=pt.update_fields)

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
                pt = user.srecord
                pt.request_new_password()
                rc += '?msg=pw-ch--success'
            else:
                rc += '?msg=pw-ch--missing'
        else:
            rc += '?msg=pw-ch--failed'

        return redirect(rc)
