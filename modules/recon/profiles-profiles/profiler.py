from recon.core.module import BaseModule
from recon.mixins.threads import ThreadingMixin
import urllib

class Module(BaseModule, ThreadingMixin):

    meta = {
        'name': 'OSINT HUMINT Profile Collector',
        'author':'Micah Hoffman (@WebBreacher)',
        'description': 'Takes each username from the profiles table and searches a variety of web sites for those users. The list of valid sites comes from the parent project at https://github.com/WebBreacher/WhatsMyName',
        'comments': (
            'Note: The global timeout option may need to be increased to support slower sites.',
            'Warning: Using this module behind a filtering proxy may cause false negatives as some of these sites may be blocked.',
        ),
        'query': 'SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL',
    }

    def module_run(self, usernames):
        # retrieve list of sites
        url = 'https://raw.githubusercontent.com/WebBreacher/WhatsMyName/master/web_accounts_list.json'
        self.verbose('Retrieving %s...' % (url))
        resp = self.request(url)
        for user in usernames: 
            self.heading('Looking up data for: %s' % user)
            self.thread(resp.json['sites'], user)

    def module_thread(self, site, user):
        d = dict(site)
        if d['valid'] == True:
            self.verbose('Checking: %s' % d['name'])
            url = d['check_uri'].replace('{account}', urllib.quote(user))
            resp = self.request(url, redirect=False)
            if resp.status_code == int(d['account_existence_code']):
                self.debug('Codes matched %s %s' % (resp.status_code, d['account_existence_code']))
                if d['account_existence_string'] in resp.text or d['account_existence_string'] in resp.headers:
                    self.add_profiles(username=user, url=url, resource=d['name'], category=d['category'])
                    self.query('DELETE FROM profiles WHERE username = ? and url IS NULL', (user,))
