from recon.core.module import BaseModule
from recon.mixins.threads import ThreadingMixin
from cookielib import CookieJar
from lxml.html import fromstring

class Module(BaseModule, ThreadingMixin):

    meta = {
        'name': 'NameChk.com Username Validator',
        'author': 'Tim Tomes (@LaNMaSteR53) and thrapt (thrapt@gmail.com)',
        'description': 'Leverages NameChk.com to validate the existance of usernames on specific web sites and updates the \'profiles\' table with the results.',
        'comments': (
            'Note: The global timeout option may need to be increased to support slower sites.',
        ),
        'query': 'SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL',
    }

    def module_run(self, usernames):
        # retrieve list of sites
        self.verbose('Retrieving site data...')
        url = 'https://namechk.com/'
        cookiejar = CookieJar()
        resp = self.request(url, cookiejar=cookiejar)
        tree = fromstring(resp.text)
        # extract sites info from the page
        names = tree.xpath('//div[@class="media record"]/@data-name')
        labels = tree.xpath('//div[@class="media record"]//h4[@class="media-heading"]/text()')
        if not len(names) == len(labels):
            self.error('Inconsistent number of sites and labels.')
            return
        # merge names and labels into a list of tuples
        sites = zip(names, labels)
        # extract token from the reponse
        token = ''.join([x.value for x in resp.cookiejar if x.name=='token'])
        # reset url for site requests
        url = 'https://namechk.com/availability/%s'
        payload = {'x': token}
        # required header for site requests
        headers = {'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}
        for username in usernames:
            self.heading(username, level=0)
            payload['q'] = username
            # validate memberships
            self.thread(sites, url, payload, headers, cookiejar)

    def module_thread(self, site, url, payload, headers, cookiejar):
        name, label = site
        fails = 1
        retries = 5
        while True:
            # build and send the request
            resp = self.request(url % (name), headers=headers, payload=payload, cookiejar=cookiejar)
            # retry a max # of times for server 500 error
            if 'error' in resp.json:
                if fails < retries:
                    fails += 1
                    continue
                self.error('%s: Unknown error!' % (label))
            else:
                username = resp.json['username']
                available = resp.json['available']
                #status = resp.json['status']
                #reason = resp.json['failed_reason']
                profile = resp.json['callback_url']
                if not available:
                    # update profiles table
                    self.add_profiles(username=username, resource=label, url=profile, category='social')
                    self.query('DELETE FROM profiles WHERE username = ? and url IS NULL', (username,))
            break
