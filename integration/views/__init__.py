from django.core.exceptions import PermissionDenied, ObjectDoesNotExist

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from ..models import Attachment


def dispatch_by_user(student_view, ugv_student_view, staff_view):
    @login_required(login_url='/authentication/login/')
    def get_view(request, **kwargs):
        if request.user.is_student:
            return student_view(request, **kwargs)
        elif request.user.is_ugv_student:
            return ugv_student_view(request, **kwargs)
        elif request.user.is_unistaff:
            return staff_view(request, **kwargs)
        else:
            raise PermissionDenied()

    return get_view


@login_required(login_url='/authentication/login/')
def download_attachment(request, *args, **kwargs):
    att_id = kwargs.get('att_id')
    att = Attachment.objects.get(pk=att_id)
    if not att:
        raise ObjectDoesNotExist()

    rc = att.fetch_content()

    response = HttpResponse(rc, content_type=att.content_type)
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(att.name)

    return response
