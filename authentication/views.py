from django.core.exceptions import *
from django.views import View
from django.http.response import Http404
from django.shortcuts import render

from .models import PerishableToken
from .forms import SetPasswordForm


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

            pt.delete()

            return render(request, self.template_done, context)

        context.update(form=form)

        return render(request, self.template_form, context)
