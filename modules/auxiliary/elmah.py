import framework
# unique to module
import os

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'source': 'database'
                        }
        self.info = {
                     'Name': 'ELMAH Log Scanner',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Checks hosts for a \'elmah.axd\' log page.',
                     'Comments': [
                                  'Source options: database, <hostname>, <path/to/infile>',
                                  'http://www.troyhunt.com/2012/01/aspnet-session-hijacking-with-google.html',
                                  'Google dorks: inurl:elmah.axd ASPXAUTH',
                                  '              inurl:elmah.axd intitle:"Error log for"'
                                  ]
                     }

    def do_run(self, params):
        self.check_for_elmah()
    
    def check_for_elmah(self):
        verbose = self.goptions['verbose']
        
        # handle sources
        source = self.options['source']
        if source == 'database':
            hosts = [x[0] for x in self.query('SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')]
            if len(hosts) == 0:
                self.error('No hosts in the database.')
                return
        elif os.path.exists(source): hosts = open(source).read().split()
        else: hosts = [source]

        # check all hosts for elmah page
        protocols = ['http', 'https']
        cnt = 0
        for host in hosts:
            for proto in protocols:
                url = '%s://%s/elmah.axd' % (proto, host)
                try:
                    resp = self.request(url, redirect=False)
                    code = resp.status_code
                except KeyboardInterrupt:
                    print ''
                    code = None
                    return
                except:
                    code = 'Error'
                if code == 200 and 'Error Log for' in resp.text:
                    self.alert('%s => %s. Possible ELMAH log page found!' % (url, code))
                    cnt += 1
                else:
                    if verbose: self.output('%s => %s' % (url, code))
        self.output('%d ELMAH log pages found.' % (cnt))