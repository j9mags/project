from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$',
        views.dispatch_by_user(
            views.StudentDashboard.as_view(),
            views.StaffDashboard.as_view()),
        name='dashboard')
]
