import framework
import __builtin__
# unique to module
import os

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'source': 'database'
                        }
        self.info = {
                     'Name': 'robots.txt/sitemap.xml Finder',
                     'Author': 'thrapt (thrapt@yahoo.com.br)',
                     'Description': 'Checks all of the hosts stored in the database for the robots.txt and sitemap.xml.',
                     'Comments': [
                                  'Source options: database, <hostname>, <path/to/infile>',
                                  ]
                     }

    def do_run(self, params):
        self.check_for_status()
    
    def check_for_status(self):
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

        # check all hosts for robots.txt and sitemap.xml
        protocols = ['http', 'https']
        filenames = ['robots.txt', 'sitemap.xml']
        cnt = 0
        for host in hosts:
            for proto in protocols:
                for filename in filenames:
                    url = '%s://%s/%s' % (proto, host, filename)
                    try:
                        resp = self.request(url, redirect=False)
                        code = resp.status_code
                    except KeyboardInterrupt:
                        print ''
                        code = None
                        return
                    except:
                        code = 'Error'
                    if code == 200:
                        self.alert('%s => %s. %s found!' % (url, code, filename))
                        self.output("\t ---")                        
                        self.output("\n".join(["\t| %s" % v for v in resp.text.splitlines()]))
                        self.output("\t ---")
                        cnt += 1
                    else:
                        if verbose: self.output('%s => %s' % (url, code))
        
        self.output('%d files found.' % (cnt))
