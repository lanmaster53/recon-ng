from recon.core.module import BaseModule
from recon.mixins.search import GoogleWebMixin
from itertools import groupby
import json
import os
import urlparse

def _optionize(s):
    return 'ghdb_%s' % (s.replace(' ', '_').lower())

def _build_options(ghdb):
    categories = []
    for key, group in groupby([x['category'] for x in sorted(ghdb, key=lambda x: x['category'])]):
        categories.append((_optionize(key), False, True, 'enable/disable the %d dorks in this category' % (len(list(group)))))
    return categories

class Module(BaseModule, GoogleWebMixin):

    with open(os.path.join(BaseModule.data_path, 'ghdb.json')) as fp:
        ghdb = json.load(fp)

    meta = {
        'name': 'Google Hacking Database',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Searches for possible vulnerabilites in a domain by leveraging the Google Hacking Database (GHDB) and the \'site\' search operator. Updates the \'vulnerabilities\' table with the results.',
        'comments': (
            'Offensive Security no longer provides access to the GHDB for Recon-ng. The included list was last updated on 8/1/2016.',
        ),
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
        'options': [
            ('dorks', None, False, 'file containing an alternate list of Google dorks'),
        ] + _build_options(ghdb),
    }

    def module_run(self, domains):
        dorks = self.ghdb
        # use alternate list of dorks if the option is set
        if self.options['dorks'] and os.path.exists(self.options['dorks']):
            with open(self.options['dorks']) as fp:
                dorks = [x.strip() for x in fp.readlines()]
        for domain in domains:
            self.heading(domain, level=0)
            base_query = 'site:%s' % (domain)
            for dork in dorks:
                # build query based on alternate list
                if isinstance(dork, basestring):
                    query = ' '.join((base_query, dork))
                    self._search(query)
                # build query based on ghdb entry
                elif isinstance(dork, dict):
                    if not dork['querystring']:
                        continue
                    if self.options[_optionize(dork['category'])]:
                        # parse the query string to extract the dork syntax
                        parsed = urlparse.urlparse(dork['querystring'])
                        params = urlparse.parse_qs(parsed.query)
                        # unparsable url
                        if 'q' not in params:
                            continue
                        query = ' '.join((base_query, params['q'][0]))
                        self._search(query)

    def _search(self, query):
        for result in self.search_google_web(query):
            host = urlparse.urlparse(result).netloc
            data = {
                'host': host,
                'reference': query,
                'example': result,
                'category': 'Google Dork',
            }
            self.add_vulnerabilities(**data)
