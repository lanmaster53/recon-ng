from recon.core.module import BaseModule
from recon.mixins.threads import ThreadingMixin
import json
import os
import urllib

class Module(BaseModule, ThreadingMixin):

    meta = {
        'name': 'OSINT HUMINT Profile Collector',
        'author':'Micah Hoffman (@WebBreacher)',
        'description': 'Takes each username from the profiles table and searches a variety of web sites for those users.',
        'comments': (
            'Note: The global timeout option may need to be increased to support slower sites.',
            'Warning: Using this module behind a filtering proxy may cause false negatives as some of these sites may be blocked.',
        ),
        'query': 'SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL',
        'options': (
            ('site_db', os.path.join(BaseModule.data_path, 'profiler_sites.json'), True, 'JSON file containing known sites and response codes'),
        ),
    }

    def module_run(self, usernames):
        # create sites lookup table
        with open(self.options['site_db']) as db_file:
            site_db = json.load(db_file)
        self.output('We have %s sites that we will check for your usernames. This will take a while.' % len(site_db['sites']))
        for user in usernames: 
            self.heading('Looking up data for: %s' % user)
            self.thread(site_db['sites'], user)

    def module_thread(self, site, user):
        d = dict(site)
        self.verbose('Checking: %s' % d['r'])
        url = d['u'] % urllib.quote(user)
        resp = self.request(url, redirect=False)
        if resp.status_code == int(d['gRC']):
            self.debug('Codes matched %s %s' % (resp.status_code, d['gRC']))
            if d['gRT'] in resp.text or d['gRT'] in resp.headers:
                self.alert('Probable match: %s' % url)
                self.add_profiles(username=user, url=url, resource=d['r'], category=d['c'])
                self.query('DELETE FROM profiles WHERE username = ? and url IS NULL', (user,))
