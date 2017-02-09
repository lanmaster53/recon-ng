from recon.core.module import BaseModule
import time

class Module(BaseModule):

    meta = {
        'name': 'Censys.io Netblock Enumerator',
        'author': 'John Askew (https://bitbucket.org/skew)',
        'description': 'Queries the censys.io API to enumerate information about netblocks.',
        'required_keys': ['censysio_id', 'censysio_secret'],
        'comments': (
            'To enumerate ports for hosts, use the following query as the SOURCE option.',
            '\tSELECT DISTINCT ip_address || \'/32\' FROM hosts WHERE ip_address IS NOT NULL',
            'Leak rates may vary. Each user\'s leak rate is listed in their Censys.io account.',
        ),
        'query': 'SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL',
        'options': (
            ('rate', .2, True, 'search endpoint leak rate (tokens/second)'),
            ('limit', True, True, 'toggle rate limiting'),
        ),
    }

    def module_run(self, netblocks):
        for netblock in netblocks:
            self.heading(netblock, level=0)
            page = 1
            while True:
                resp = self._get_page(netblock, page)
                if resp.status_code != 200:
                    self.error('Error: \'%s\'' % (resp.json.get('error')))
                    break
                self._load_results(resp)
                if resp.json.get('metadata').get('page') >= resp.json.get('metadata').get('pages'):
                    break
                self.verbose('Fetching the next page of results...')
                page += 1

    def _get_page(self, netblock, page):
        payload = {
            'query': 'ip:{}'.format(netblock),
            'page': page,
            'fields': ['ip', 'protocols']
        }
        resp = self.request(
            'https://censys.io/api/v1/search/ipv4',
            payload=payload,
            auth=(
                self.keys.get('censysio_id'),
                self.keys.get('censysio_secret')
            ),
            method='POST',
            content='JSON',
        )
        if self.options['limit']:
            time.sleep(1 / self.options['rate'])
        return resp

    def _load_results(self, resp):
        for result in resp.json.get('results'):
            ip_address = result.get('ip')
            for service in result.get('protocols'):
                port, protocol = service.split('/')
                self.add_ports(ip_address=ip_address, port=port, protocol=protocol)
