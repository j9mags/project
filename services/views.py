from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt

from xhtml2pdf import pisa
from io import StringIO

import base64
import imgkit
import json

from integration.models import ContentVersion
from .s3 import upload


@method_decorator(csrf_exempt, name='dispatch')
class HtmlToImageView(View):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        payload = json.loads(request.body.decode('utf-8'))
        img_format = payload.get('format', 'png')
        sources = payload.get('sources', [])

        if sources and not isinstance(sources, (list, tuple)):
            sources = [sources]

        data = {img_format: []}
        tmp_fname = '/tmp/out.{}'.format(img_format)

        for html in sources:
            imgkit.from_string(html, tmp_fname, options={"xvfb": ""})
            with open(tmp_fname, 'rb') as img:
                data[img_format].append(base64.b64encode(img.read()).decode('utf-8'))

        return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
class HtmlToPDFView(View):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        payload = json.loads(request.body.decode('utf-8'))
        content = payload.get('html', '')
        
        tmp_fname = '/tmp/out.pdf'
        pdf = None
        with open(tmp_fname, "w+b") as f:
            pdf = pisa.CreatePDF(content, dest=f)

        if pdf.err:
            return JsonResponse({'error': json.dumps(pdf.err)})
        
        bstream = open(tmp_fname, 'rb').read()
        return JsonResponse({'pdf': base64.encodebytes(bstream).decode('utf-8')})


@method_decorator(csrf_exempt, name='dispatch')
class UploadToS3(View):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)

        if pk is None:
            return JsonResponse(status=400, data={"error": "MissingRecordId"})
        
        try:
            cv = ContentVersion.objects.get(pk=pk)
        except:
            return JsonResponse(status=404, data={"error": "ContentVersionNotFound"})

        payload = json.loads(request.body.decode('utf-8'))
        sobject = payload.get("sobject", None)
        parentId = payload.get("parentId", None)
        path = (sobject + '/' if sobject is not None else '') + \
               (parentId + '/' if parentId is not None else '') + \
               cv.path_on_client
        
        try:
            blob = cv.fetch_content()
            url = upload(path, blob)
        except Exception as e:
            return JsonResponse(status=500, data={"error": "UnknownError", "message": str(e)})

        return JsonResponse({"url": url})
