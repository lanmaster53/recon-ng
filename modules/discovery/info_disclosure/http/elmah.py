import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'ELMAH Log Scanner',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Checks hosts for a \'elmah.axd\' log page.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                                  'http://www.troyhunt.com/2012/01/aspnet-session-hijacking-with-google.html',
                                  'Google dorks: inurl:elmah.axd ASPXAUTH',
                                  '              inurl:elmah.axd intitle:"Error log for"'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.check_for_elmah()
    
    def check_for_elmah(self):
        verbose = self.options['verbose']['value']
        
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return

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
                    return
                except:
                    code = 'Error'
                if code == 200 and 'Error Log for' in resp.text:
                    self.alert('%s => %s. Possible ELMAH log page found!' % (url, code))
                    cnt += 1
                else:
                    if verbose: self.output('%s => %s' % (url, code))
        self.output('%d ELMAH log pages found.' % (cnt))
