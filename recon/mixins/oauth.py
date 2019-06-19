import re
import socket
import urllib.parse
import webbrowser

class ExplicitOauthMixin(object):

    def get_explicit_oauth_token(self, resource, scope, authorize_url, access_url):
        token_name = resource+'_token'
        token = self.get_key(token_name)
        if token:
            return token
        client_id = self.get_key(resource+'_api')
        client_secret = self.get_key(resource+'_secret')
        port = 31337
        redirect_uri = f"http://localhost:{port}"
        payload = {'response_type': 'code', 'client_id': client_id, 'scope': scope, 'state': self.get_random_str(40), 'redirect_uri': redirect_uri}
        authorize_url = f"{authorize_url}?{urllib.parse.urlencode(payload)}"
        w = webbrowser.get()
        w.open(authorize_url)
        # open a socket to receive the access token callback
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.listen(1)
        conn, addr = sock.accept()
        data = conn.recv(1024)
        conn.sendall('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><head><title>Recon-ng</title></head><body>Response received. Return to Recon-ng.</body></html>')
        conn.close()
        # process the received data
        if 'error_description' in data:
            self.error(urllib.parse.unquote_plus(re.search(r'error_description=([^\s&]*)', data).group(1)))
            return None
        authorization_code = re.search(r'code=([^\s&]*)', data).group(1)
        payload = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': redirect_uri, 'client_id': client_id, 'client_secret': client_secret}
        resp = self.request('POST', access_url, data=payload)
        if 'error' in resp.json():
            self.error(resp.json()['error_description'])
            return None
        access_token = resp.json()['access_token']
        self.add_key(token_name, access_token)
        return access_token
