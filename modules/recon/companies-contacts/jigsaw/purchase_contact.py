from recon.core.module import BaseModule
import time

class Module(BaseModule):

    meta = {
        'name': 'Jigsaw - Single Contact Retriever',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Retrieves a single complete contact from the Jigsaw.com API using points from the given account.',
        'required_keys': ['jigsaw_username', 'jigsaw_password', 'jigsaw_api'],
        'comments': (
            'Account Point Cost: 5 points per request.',
            'This module is typically used to validate email address naming conventions and gather alternative social engineering information.',
        ),
        'options': (
            ('contact', None, True, 'jigsaw contact id'),
        ),
    }

    def module_run(self):
        username = self.keys.get('jigsaw_username')
        password = self.keys.get('jigsaw_password')
        key = self.keys.get('jigsaw_api')
        url = 'https://www.jigsaw.com/rest/contacts/%s.json' % (self.options['contact'])
        payload = {'token': key, 'username': username, 'password': password, 'purchaseFlag': 'true'}
        resp = self.request(url, payload=payload, redirect=False)
        if resp.json: jsonobj = resp.json
        else:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return
        # handle output
        contacts = jsonobj['contacts']
        header = ['Item', 'Info']
        for contact in contacts:
            tdata = []
            for key in contact:
                tdata.append((key.title(), contact[key]))
            self.table(tdata, header=header, title='Jigsaw %s' % (contact['contactId']))
