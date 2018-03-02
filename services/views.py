from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt

import base64
import imgkit
import json


@method_decorator(csrf_exempt, name='dispatch')
class HtmlToImageView(View):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        payload = json.loads(request.body.decode('utf-8'))
        img_format = payload.get('format', 'png')
        sources = payload.get('sources', [])

        if sources and not isinstance(sources, (list, tuple)):
            sources = [sources]

        data = {img_format: [], 'sources': sources, 'payload': payload}
        tmp_fname = '/tmp/out.{}'.format(img_format)

        for html in sources:
            imgkit.from_string(html, tmp_fname, options={"xvfb": ""})
            with open(tmp_fname, 'rb') as img:
                data[img_format].append(base64.encodestring(img.read()))

        return JsonResponse(data)
