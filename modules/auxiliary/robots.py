import framework
import __builtin__
# unique to module
import os
import gzip
from StringIO import StringIO

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'source': 'database'
                        }
        self.info = {
                     'Name': 'robots.txt/sitemap.xml Finder',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Description': 'Checks all of the hosts stored in the database for the robots.txt, sitemap.xml and sitemap.xml.gz.',
                     'Comments': [
                                  'Source options: database, <hostname>, <path/to/infile>',
                                  ]
                     }

    def do_run(self, params):
        self.check_for_status()
    
    def uncompress(self, data_gz):
        inbuffer = StringIO(data_gz)
        data_ct = ''
        f = gzip.GzipFile(mode='rb', fileobj=inbuffer)
        try:
            data_ct = f.read()
        except IOError:
            pass
        f.close()
        return data_ct     
    
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

        # check all hosts for robots.txt, sitemap.xml and sitemap.xml.gz
        protocols = ['http', 'https']
        # filename and string used to verify the file
        filetypes = [('robots.txt', 'user-agent:'), ('sitemap.xml', '<?xml'), ('sitemap.xml.gz', '<?xml')]
        cnt = 0
        for host in hosts:
            for proto in protocols:
                for (filename, verify) in filetypes:
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
                        # uncompress if necessary
                        text = ('.gz' in filename and self.uncompress(resp.text)) or resp.text
                        # check for file type since many custom 404s are returned as 200s 
                        if (verify in text.lower()):
                            self.alert('%s => %s. %s found!' % (url, code, filename))
                            self.output("\t ---")                        
                            self.output("\n".join(["\t| %s" % v for v in text.splitlines()]))
                            self.output("\t ---")
                            cnt += 1
                        else:
                            self.output('%s => %s. %s invalid!' % (url, code, filename))
                    else:
                        if verbose: self.output('%s => %s' % (url, code))
        
        self.output('%d files found.' % (cnt))
