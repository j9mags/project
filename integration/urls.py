from django.conf.urls import url

from .views import dispatch_by_user, download_attachment
from .views import staff, student, ugv_student

urlpatterns = [
    url(r'^onboarding/(?P<step>{})/$'.format('|'.join(['({})'.format(x) for x in student.Onboarding.steps])),
        dispatch_by_user(
            student.Onboarding.as_view(),
            ugv_student.Onboarding.as_view(),
            None
        ), name='onboarding'),
    url(r'^onboarding/$', dispatch_by_user(
        student.Onboarding.as_view(),
        ugv_student.Onboarding.as_view(),
        None
    ), name='onboarding'),
    url(r'^contact/(?P<pk>(.+)|(new))/$', dispatch_by_user(
        student.ContactDetails.as_view(),
        ugv_student.ContactDetails.as_view(),
        None
    ), name='contact'),
    url(r'^payment/$', dispatch_by_user(
        student.PaymentDetails.as_view(),
        ugv_student.PaymentDetails.as_view(),
        None
    ), name='payment'),

    url(r'^review/(?P<uuid>.+)/(?P<action>(confirm)|(discard))/$',
        staff.FileUploadAction.as_view(), name='upload_action'),
    url(r'^review/(?P<uuid>.+)/$', staff.FileUpload.as_view(), name='upload_review'),
    url(r'^student/register/$', staff.StudentRegister.as_view(), name='student_register'),
    url(r'^student/(?P<pk>.+)/$', staff.StudentReview.as_view(), name='student_review'),
    url(r'^students/$', staff.DashboardStudents.as_view(), name='students'),
    url(r'^ugvers/$', staff.DashboardUGVers.as_view(), name='ugvers'),
    url(r'^bulk/$', staff.BulkActions.as_view(), name='students_bulk'),
    url(r'^university/$', staff.DashboardUniversity.as_view(), name='university'),
    url(r'^course/(?P<pk>.+)/$', staff.CourseReview.as_view(), name='course_review'),
    url(r'^courses/$', staff.DashboardCourses.as_view(), name='courses'),
    url(r'^application/(?P<pk>.+)/$', staff.UGVApplicationReview.as_view(), name='application_review'),
    url(r'^applications/$', staff.DashboardUGVApplications.as_view(), name='applications'),
    url(r'^invoices/$', staff.DashboardInvoices.as_view(), name='invoices'),

    url(r'^attachment/(?P<att_id>.+)/$', download_attachment, name='download_attachment'),
    url(r'^language/$',
        dispatch_by_user(
            student.SetLanguage.as_view(),
            ugv_student.SetLanguage.as_view(),
            staff.SetLanguage.as_view()),
        name='language'),
    url(r'^language/(?P<language>.+)/$',
        dispatch_by_user(
            student.SetLanguage.as_view(),
            ugv_student.SetLanguage.as_view(),
            staff.SetLanguage.as_view()),
        name='setlanguage'),
    url(r'^$',
        dispatch_by_user(
            student.Dashboard.as_view(),
            ugv_student.Dashboard.as_view(),
            staff.DashboardHome.as_view()),
        name='dashboard'),
]
