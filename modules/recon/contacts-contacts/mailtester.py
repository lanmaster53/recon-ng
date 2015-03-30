from recon.core.module import BaseModule
from io import StringIO
from lxml import etree

class Module(BaseModule):

    meta = {
        'name': 'MailTester Email Validator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Leverages MailTester.com to validate email addresses.',
        'query': 'SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL',
    }

    def module_run(self, emails):
        url = 'http://www.mailtester.com/testmail.php'
        payload = {'lang':'en'}
        for email in emails:
            payload['email'] = email
            resp = self.request(url, method='POST', payload=payload)
            tree = etree.parse(StringIO(resp.text), etree.HTMLParser())
            msg_list = tree.xpath('//table[2]/tr[last()]/td[last()]/text()')
            msg = ' '.join([x.strip() for x in msg_list])
            output = self.alert if 'is valid' in msg else self.output
            output('{0} => {1}'.format(email, msg))
