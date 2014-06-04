import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT company FROM companies WHERE company IS NOT NULL ORDER BY company')
        self.info = {
                     'Name': 'LinkedIn Authenticated Contact Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests contacts from the LinkedIn.com API using an authenticated connections network. Updates the \'contacts\' table with the results.'
                     }

    def get_linkedin_access_token(self):
        token_name = 'linkedin_token'
        try:
            return self.get_key(token_name)
        except:
            pass
        import urllib
        import webbrowser
        import socket
        linkedin_key = self.get_key('linkedin_api')
        linkedin_secret = self.get_key('linkedin_secret')
        port = 31337
        redirect_uri = 'http://127.0.0.1:%d' % (port)
        url = 'https://www.linkedin.com/uas/oauth2/authorization'
        payload = {'response_type': 'code', 'client_id': linkedin_key, 'scope': 'r_basicprofile r_network', 'state': 'thisisaverylongstringusedforstate', 'redirect_uri': redirect_uri}
        authorize_url = '%s?%s' % (url, urllib.urlencode(payload))
        w = webbrowser.get()
        w.open(authorize_url)
        # open a socket to receive the access token callback
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.listen(1)
        conn, addr = sock.accept()
        data = conn.recv(1024)
        conn.sendall('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><head><title>Recon-ng</title></head><body>Authorization code received. Return to Recon-ng.</body></html>')
        conn.close()
        # process the received access token
        authorization_code = re.search('code=([^&]*)', data).group(1)
        url = 'https://www.linkedin.com/uas/oauth2/accessToken'
        payload = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': redirect_uri, 'client_id': linkedin_key, 'client_secret': linkedin_secret}
        resp = self.request(url, method='POST', payload=payload)
        if 'error' in resp.json:
            self.error(resp.json['error_description'])
            return None
        access_token = resp.json['access_token']
        self.add_key(token_name, access_token)
        return access_token

    def module_run(self, companies):
        access_token = self.get_linkedin_access_token()
        if access_token is None: return
        count = 25
        url = 'https://api.linkedin.com/v1/people-search:(people:(id,first-name,last-name,headline,location:(name,country:(code))))'
        cnt, tot = 0, 0
        for company in companies:
            self.heading(company, level=0)
            payload = {'format': 'json', 'company-name': company, 'current-company': 'true', 'count': count, 'oauth2_access_token': access_token}
            page = 1
            while True:
                resp = self.request(url, payload=payload)
                jsonobj = resp.json
                if 'errorCode' in jsonobj:
                    if jsonobj['status'] == 401:
                        # renew token
                        self.delete_key('linkedin_token')
                        payload['oauth2_access_token'] = self.get_linkedin_access_token()
                        continue
                    self.error(jsonobj['message'])
                    break
                if not 'values' in jsonobj['people']:
                    break
                for contact in jsonobj['people']['values']:
                    # the headline field does not exist when a connection is private
                    # only public connections can be harvested beyond the 1st degree
                    if 'headline' in contact:
                        fname = self.html_unescape(re.split('[\s]',contact['firstName'])[0])
                        lname = self.html_unescape(re.split('[,;]',contact['lastName'])[0])
                        title = self.html_unescape(contact['headline'])
                        region = re.sub('(?:Greater\s|\sArea)', '', self.html_unescape(contact['location']['name']).title())
                        country = self.html_unescape(contact['location']['country']['code']).upper()
                        self.output('%s %s - %s (%s - %s)' % (fname, lname, title, region, country))
                        tot += 1
                        cnt += self.add_contacts(first_name=fname, last_name=lname, title=title, region=region, country=country)
                if not '_start' in jsonobj['people']:
                    break
                if jsonobj['people']['_start'] + jsonobj['people']['_count'] == jsonobj['people']['_total']:
                    break
                payload['start'] = page * jsonobj['people']['_count']
                page += 1
        self.summarize(cnt, tot)
