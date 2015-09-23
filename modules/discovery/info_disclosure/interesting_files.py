from recon.core.module import BaseModule
import warnings
import gzip
from StringIO import StringIO

class Module(BaseModule):

    meta = {
        'name': 'Interesting File Finder',
        'author': 'Tim Tomes (@LaNMaSteR53), thrapt (thrapt@gmail.com), Jay Turla (@shipcod3), and Mark Jeffery',
        'description': 'Checks hosts for interesting files in predictable locations.',
        'comments': (
            'Files: robots.txt, sitemap.xml, sitemap.xml.gz, crossdomain.xml, phpinfo.php, test.php, elmah.axd, server-status, jmx-console/, admin-console/, web-console/',
            'Google Dorks:',
            '\tinurl:robots.txt ext:txt',
            '\tinurl:elmah.axd ext:axd intitle:"Error log for"',
            '\tinurl:server-status "Apache Status"',
        ),
        'query': 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL',
        'options': (
            ('download', True, True, 'download discovered files'),
            ('protocol', 'http', True, 'request protocol'),
            ('port', 80, True, 'request port'),
        ),
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

    def module_run(self, hosts):
        download = self.options['download']
        protocol = self.options['protocol']
        port = self.options['port']
        # ignore unicode warnings when trying to ungzip text type 200 repsonses
        warnings.simplefilter("ignore")
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
            for (filename, verify) in filetypes:
                url = '%s://%s:%d/%s' % (protocol, host, port, filename)
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
                        # urls that end with '/' are not necessary to download
                        if download and not filename.endswith("/"):
                            filepath = '%s/%s_%s_%s' % (self.workspace, protocol, host, filename)
                            dl = open(filepath, 'w')
                            dl.write(resp.text.encode(resp.encoding) if resp.encoding else resp.text)
                            dl.close()
                        cnt += 1
                    else:
                        self.output('%s => %s. \'%s\' found but unverified.' % (url, code, filename))
                else:
                    self.verbose('%s => %s' % (url, code))
        self.output('%d interesting files found.' % (cnt))
        if download: self.output('...downloaded to \'%s/\'' % (self.workspace))
