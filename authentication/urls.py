from django.conf.urls import url

from django.contrib.auth.views import LoginView

from . import views


urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='authentication.login'),
    url(r'^password/set/$', views.PasswordSet.as_view()),
]
