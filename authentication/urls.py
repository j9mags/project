from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^login/$', views.UserLogin.as_view(), name='login'),
    url(r'^logout/$', views.UserLogout.as_view(), name='logout'),
    url(r'^password/set/$', views.PasswordSet.as_view(), name='password-set'),
    url(r'^password/change/$', views.PasswordChange.as_view(), name='password-change'),
]
