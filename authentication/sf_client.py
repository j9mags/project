import requests


class SalesforceApi(object):
    def __init__(self):
        self._access_data = {}

    def _auth(self):
        if self._access_data:
            return True

        data = {
            'grant_type': 'password',
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SEC,
            'username': self.USERNAME,
            'password': self.PASSWORD
        }
        res = requests.post(self.LOGIN_URL, data=data)

        if res.status_code == 200:
            self._access_data = res.json()
        else:
            self._access_data = {}

        return True if self._access_data else False

    def get(self, endpoint, params={}, public=False):
        rc = public or self._auth()

        if not rc:
            raise

        headers = {}
        if not public:
            if not endpoint.startswith('http'):
                endpoint = '/services/data/v39.0/sobjects/' + endpoint

            headers.update(
                Authorization='Bearer {access_token}'.format(**self._access_data)
            )

        url = self._access_data.get('instance_url', '') + endpoint
        print('[GET] ' + url + '?' + str(params))

        res = requests.get(url, params=params, headers=headers)
        if res.status_code == 200:
            return res.json()
        else:
            return res.content
