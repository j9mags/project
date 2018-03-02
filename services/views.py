from django.http import JsonResponse
from django.views.generic.base import View

import imgkit
import base64


class HtmlToImageView(View):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        payload = request.POST
        img_format = payload.get('format', 'png')
        sources = payload.get('sources', [])

        if sources and not isinstance(sources, (list, tuple)):
            sources = [sources]

        data = {img_format: []}
        tmp_fname = '/tmp/out.{}'.format(img_format)

        for html in sources:
            imgkit.from_string(html, tmp_fname, options={"xvfb": ""})
            with open(tmp_fname, 'rb') as img:
                data[img_format].append(base64.encodestring(img.read()))

        return JsonResponse(data)
