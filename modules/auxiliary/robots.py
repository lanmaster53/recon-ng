import framework
# unique to module
import gzip
from StringIO import StringIO

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'robots.txt/sitemap.xml Finder',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Description': 'Checks hosts for a robots.txt, sitemap.xml and sitemap.xml.gz file.',
                     'Comments': [
                                  'Source options: db, <hostname>, <path/to/infile>',
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
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
        verbose = self.options['verbose']['value']
        
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return

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
                        return
                    except:
                        code = 'Error'
                    if code == 200:
                        # uncompress if necessary
                        text = ('.gz' in filename and self.uncompress(resp.text)) or resp.text
                        # check for file type since many custom 404s are returned as 200s 
                        if (verify in text.lower()):
                            self.alert('%s => %s. %s found!' % (url, code, filename))
                            cnt += 1
                        else:
                            self.output('%s => %s. %s invalid!' % (url, code, filename))
                    else:
                        if verbose: self.output('%s => %s' % (url, code))
        
        self.output('%d files found.' % (cnt))
