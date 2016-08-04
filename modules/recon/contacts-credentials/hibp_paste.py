from recon.core.module import BaseModule
import os
import time
import urllib

class Module(BaseModule):

    meta = {
        'name': 'Have I been pwned? Paste Search',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Leverages the haveibeenpwned.com API to determine if email addresses have been published to various paste sites. Adds compromised email addresses to the \'credentials\' table.',
        'comments': (
            'Paste sites supported: Pastebin, Pastie, Slexy, Ghostbin, QuickLeak, JustPaste, AdHocUrl, and OptOut.'
            'The HIBP API is rate limited to 1 request per 1.5 seconds.',
        ),
        'query': 'SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL',
        'options': (
            ('download', True, True, 'download pastes'),
        ),
    }

    def module_run(self, accounts):
        # check back often for new paste sources
        sites = {
            'Pastebin': 'http://pastebin.com/raw.php?i=%s',
            'Pastie': 'http://pastie.org/pastes/%s/text',
            'Slexy': 'http://slexy.org/raw/%s',
            'Ghostbin': 'https://ghostbin.com/paste/%s/raw',
            'QuickLeak': 'http://www.quickleak.ir/%s',
            'JustPaste': 'https://justpaste.it/%s',
            'AdHocUrl': '%s',
            }
        # retrieve status
        base_url = 'https://haveibeenpwned.com/api/v2/%s/%s'
        endpoint = 'pasteaccount'
        for account in accounts:
            resp = self.request(base_url % (endpoint, urllib.quote(account)))
            rcode = resp.status_code
            if rcode == 404:
                self.verbose('%s => Not Found.' % (account))
            elif rcode == 400:
                self.error('%s => Bad Request.' % (account))
                continue
            else:
                for paste in resp.json:
                    download = False
                    fileurl = paste['Id']
                    if paste['Source'] in sites:
                        fileurl = sites[paste['Source']] % (paste['Id'])
                        download = self.options['download']
                    elif self.options['download'] == True:
                        self.alert('Download not available for %s pastes.' % (paste['Source']))
                    self.alert('%s => Paste found! Seen in a %s on %s (%s).' % (account, paste['Source'], paste['Date'], fileurl))
                    if download == True:
                        resp = self.request(fileurl)
                        if resp.status_code == 200:
                            filepath = '%s/%s.txt' % (self.workspace, _safe_file_name(fileurl))
                            if not os.path.exists(filepath):
                                dl = open(filepath, 'w')
                                dl.write(resp.text.encode(resp.encoding) if resp.encoding else resp.text)
                                dl.close()
                            self.verbose('Paste stored at \'%s\'.' % (filepath))
                        else:
                            self.alert('Paste could not be downloaded (%s).' % (fileurl))
                self.add_credentials(account)
            time.sleep(1.6)

def _safe_file_name(s):
    return "".join(c for c in s if c.isalnum()).rstrip()
