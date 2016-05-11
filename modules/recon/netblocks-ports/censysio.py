from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'censys.io port lookup by netblock',
        'author': 'John Askew (https://bitbucket.org/skew)',
        'description': 'Queries censys.io to enumerate open ports for a netblock.',
        'comments': (
            'To enumerate ports for hosts, use the following query as the SOURCE option.',
            '\tSELECT DISTINCT ip_address || \'/32\' FROM hosts WHERE ip_address IS NOT NULL',
        ),
        'query': 'SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL',
    }

    def module_run(self, netblocks):
        api_id = self.get_key('censysio_id')
        api_secret = self.get_key('censysio_secret')
        url = 'https://censys.io/api/v1/search/ipv4'
        for netblock in netblocks:
            self.heading(netblock, level=0)
            payload = {
                'query': 'ip:{}'.format(netblock),
            }
            resp = self.request(
                url,
                payload=payload,
                auth=(api_id, api_secret),
                method='POST',
                content='JSON',
            )
            if resp.json.get('status') != 'ok':
                self.error('Error when querying censys.io for \'{}\''.format(host))
                continue
            # handle paging?
            for result in resp.json.get('results'):
                ip_address = result.get('ip')
                for service in result.get('protocols'):
                    port, protocol = service.split('/')
                    self.add_ports(ip_address=ip_address, port=port, protocol=protocol)
