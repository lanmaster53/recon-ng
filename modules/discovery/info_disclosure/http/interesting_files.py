import framework
# unique to module
import warnings
import gzip
from StringIO import StringIO

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.register_option('download', True, 'yes', 'download discovered files')
        self.register_option('port', 80, 'no', 'request port')
        self.info = {
                     'Name': 'Interesting File Finder',
                     'Author': 'Tim Tomes (@LaNMaSteR53), thrapt (thrapt@gmail.com), and Jay Turla (@shipcod3)',
                     'Description': 'Checks hosts for interesting files in predictable locations.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                                  'Files: robots.txt, sitemap.xml, sitemap.xml.gz, crossdomain.xml, phpinfo.php, test.php, elmah.axd, server-status/, jmx-console/, admin-console/, web-console/',
                                  'Google Dorks:',
                                  '%sinurl:robots.txt ext:txt' % (self.spacer),
                                  '%sinurl:elmah.axd ext:axd intitle:"Error log for"' % (self.spacer),
                                  ]
                     }

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

    def module_run(self):
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        download = self.options['download']['value']
        port = self.options['port']['value']
        # ignore unicode warnings when trying to ungzip text type 200 repsonses
        warnings.simplefilter("ignore")
        protocols = ['http', 'https']
        # (filename, string to search for to prevent false positive)
        filetypes = [
                     ('robots.txt', 'user-agent:'),
                     ('sitemap.xml', '<?xml'),
                     ('sitemap.xml.gz', '<?xml'),
                     ('crossdomain.xml', '<?xml'),
                     ('phpinfo.php', 'phpinfo()'),
                     ('test.php', 'phpinfo()'),
                     ('elmah.axd', 'Error Log for'),
                     ('server-status', '>Apache Status<'),
                     ('jmx-console/', 'JBoss'), #JBoss 5.1.0.GA
                     ('admin-console/', 'index.seam'), #JBoss 5.1.0.GA
                     ('web-console/', 'Administration'), #JBoss 5.1.0.GA
                     ]
        cnt = 0
        for host in hosts:
            for proto in protocols:
                for (filename, verify) in filetypes:
                    if port != 80:
                        url = '%s://%s:%d/%s' % (proto, host,port, filename)
                    else:
                        url = '%s://%s/%s' % (proto, host, filename)
                    try:
                        resp = self.request(url, timeout=2, redirect=False)
                        code = resp.status_code
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    except:
                        code = 'Error'
                    if code == 200:
                        # uncompress if necessary
                        text = ('.gz' in filename and self.uncompress(resp.text)) or resp.text
                        # check for file type since many custom 404s are returned as 200s
                        if verify.lower() in text.lower():
                            self.alert('%s => %s. \'%s\' found!' % (url, code, filename))
                            #The / check is for urls that end with /. They do not necessarily denote a "file" 
                            if download and not filename.endswith("/"):
                                filepath = '%s/%s_%s_%s' % (self.workspace, proto, host, filename)
                                dl = open(filepath, 'wb')
                                dl.write(resp.text.encode(resp.encoding) if resp.encoding else resp.text)
                                dl.close()
                            cnt += 1
                        else:
                            self.output('%s => %s. \'%s\' found but unverified.' % (url, code, filename))
                    else:
                        self.verbose('%s => %s' % (url, code))
        self.output('%d interesting files found.' % (cnt))
        if download: self.output('...downloaded to \'%s/\'' % (self.workspace))
