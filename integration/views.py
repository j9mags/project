from django.core.exceptions import PermissionDenied

from django.contrib.auth.decorators import login_required


def dispatch_by_user(student_view, staff_view):
    @login_required(login_url='/authentication/login/')
    def get_view(request, **kwargs):
        if request.user.is_student():
            return student_view(request, **kwargs)
        elif request.user.is_unistaff():
            return staff_view(request, **kwargs)
        else:
            raise PermissionDenied()

    return get_view
