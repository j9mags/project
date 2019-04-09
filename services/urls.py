from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'html2img/', views.HtmlToImageView.as_view(), name='html2image'),
    url(r'html2pdf/', views.HtmlToPDFView.as_view(), name='html2pdf'),
]