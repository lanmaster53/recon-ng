import framework
# unique to module
import ssl
from M2Crypto import X509

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('url', None, 'yes', 'The host to check for subject alternative names (SAN)')
        self.register_option('port', 443, 'yes', 'The port to grab the SSL cert.')
        self.info = {
                     'Name': 'SSL SAN Lookup',
                     'Author': 'Zach Grace (@ztgrace)',
                     'Description': 'This module will parse the SSL certificate for the provided URL and enumerate the subject alternative names',
                     'Comments': []
                     }

    def module_run(self):
        url = self.options['url']['value']
        port = self.options['port']['value']
        try:
            cert = ssl.get_server_certificate((url, port))
            # fix the cert format for M2Crypto
            cert = cert.replace('-----END CERTIFICATE-----','\n-----END CERTIFICATE-----')
            x509 = X509.load_cert_string(cert)
            sans = x509.get_ext('subjectAltName').get_value()
            sans = sans.replace('DNS:', '')
            for name in sans.split(', '):
                self.alert(name)
        except:
            self.error('Unable to retrieve SSL certificate from %s:%s' % (url,port))
