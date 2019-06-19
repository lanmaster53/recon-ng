import hashlib
import hmac
import sys
import time


class PwnedlistMixin(object):

    def build_pwnedlist_payload(self, payload, method, key, secret):
        timestamp = int(time.time())
        payload['ts'] = timestamp
        payload['key'] = key
        msg = f"{key}{timestamp}{method}{secret}"
        encoding = sys.getdefaultencoding()
        hm = hmac.new(bytes(secret, encoding), bytes(msg, encoding), hashlib.sha1)
        payload['hmac'] = hm.hexdigest()
        return payload

    def get_pwnedlist_leak(self, leak_id):
        # check if the leak has already been retrieved
        leak = self.query('SELECT * FROM leaks WHERE leak_id=?', (leak_id,))
        if leak:
            leak = dict(zip([x[0] for x in self.get_columns('leaks')], leak[0]))
            del leak['module']
            return leak
        # set up the API call
        key = self.get_key('pwnedlist_api')
        secret = self.get_key('pwnedlist_secret')
        url = 'https://api.pwnedlist.com/api/1/leaks/info'
        base_payload = {'leakId': leak_id}
        payload = self.build_pwnedlist_payload(base_payload, 'leaks.info', key, secret)
        # make the request
        resp = self.request('GET', url, params=payload)
        if resp.status_code != 200:
            self.error(f"Error retrieving leak data.{os.linesep}{resp.text}")
            return
        leak = resp.json()['leaks'][0]
        # normalize the leak for storage
        normalized_leak = {}
        for item in leak:
            value = leak[item]
            if type(value) == list:
                value = ', '.join(value)
            normalized_leak[item] = value
        return normalized_leak
