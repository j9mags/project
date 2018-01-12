from django.conf.urls import url

from . import views
from . import views_student as student
from . import views_staff as staff

urlpatterns = [
    url(r'^onboarding/(?P<step>{})/$'.format('|'.join(['({})'.format(x) for x in student.Onboarding.steps])),
        student.Onboarding.as_view(), name='onboarding'),
    url(r'^onboarding/$',student.Onboarding.as_view(), name='onboarding'),
    url(r'^contact/(?P<pk>(.+)|(new))/$', student.ContactDetails.as_view(), name='contact'),
    url(r'^payment/$', student.PaymentDetails.as_view(), name='payment'),
    url(r'^attachment/(?P<att_id>.+)/$', student.DownloadAttachment.as_view(), name='download_attachment'),

    url(r'^review/(?P<uuid>.+)/(?P<action>(confirm)|(discard))/$',
        staff.FileUploadAction.as_view(), name='upload_action'),
    url(r'^review/(?P<uuid>.+)/$', staff.FileUpload.as_view(), name='upload_review'),
    url(r'^student/register/$', staff.StudentRegister.as_view(), name='student_register'),
    url(r'^student/(?P<pk>.+)/$', staff.StudentReview.as_view(), name='student_review'),
    url(r'^students/$', staff.DashboardStudents.as_view(), name='students'),
    url(r'^bulk/$', staff.BulkActions.as_view(), name='students_bulk'),
    url(r'^university/$', staff.DashboardUniversity.as_view(), name='university'),
    url(r'^course/(?P<pk>.+)/$', staff.CourseReview.as_view(), name='course_review'),
    url(r'^courses/$', staff.DashboardCourses.as_view(), name='courses'),

    url(r'^language/$',
        views.dispatch_by_user(
            student.SetLanguage.as_view(),
            staff.SetLanguage.as_view()),
        name='language'),
    url(r'^$',
        views.dispatch_by_user(
            student.Dashboard.as_view(),
            staff.DashboardHome.as_view()),
        name='dashboard'),
]
