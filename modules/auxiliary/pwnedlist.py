import _cmd
import __builtin__
# unique to module
import os
import sqlite3
import urllib2
import urllib
import re
import sys

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'source': 'db',
                        'user-agent': __builtin__.goptions['user-agent'],
                        'verbose': True,
                        }

    def do_info(self, params):
        print ''
        print 'Leverages PwnedList.com to determine if email addresses are associated with breached credentials.'
        print ''
        print 'Source options: db* | email@address | path/to/infile'
        print ''
        print '* db will be updated to reflect results'
        print ''

    def do_run(self, params):
        self.check_pwned()

    def check_pwned(self):
        verbose = self.options['verbose']
        user_agent = self.options['user-agent']
        source = self.options['source']
        # handle sources
        if source == 'db':
            conn = sqlite3.connect(self.dbfilename)
            c = conn.cursor()
            emails = [x[0] for x in c.execute('SELECT DISTINCT email FROM contacts WHERE email != "" ORDER BY email').fetchall()]
            conn.close()
            if len(emails) == 0:
                self.error('No email addresses in the db.')
                return
        elif '@' in source: emails = [source]
        elif os.path.exists(source): emails = open(source).read().split()
        else:
            self.error('Invalid source: %s' % (source))
            return
        
        pattern = "class='query_result_footer'>... we found your email in our database a total of (\d+?) times. It was last seen on ([\d-]+?). Please read on. <div"
        i, pwned = 0, 0
        while i < len(emails):
            status = None
            email = emails[i].encode('utf-8')
            url = 'http://pwnedlist.com/query'
            values = {'query_input' : email,
                      'query_input_hash' : 'empty',
                      'submit' : 'CHECK' }
            headers = { 'User-Agent' : user_agent }
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data, headers)
            try: response = self.web_req(req)
            except KeyboardInterrupt:
                sys.stdout.write('\n')
                break
            except urllib2.HTTPError as e: response = e
            except Exception as e:
                try: self.error('Error: %s.' % (e.reason))
                except: self.error('Unknown Error.')
                return
            the_page = response.read()
            if 'Gotcha!' in the_page:
                self.error('Hm... Got a captcha.')
                return
            elif '>NOPE!<' in the_page:
                status = 'safe'
                if verbose: print '[*] %s seems %s.' % (email, status)
            elif '>YES<' in the_page:
                status = 'pwned'
                m = re.search(pattern, the_page)
                qty = m.group(1)
                last = m.group(2)
                print '[!] %s has been compromised %s times and as recent as %s.' % (email, qty, last)
                pwned += 1
            else:
                self.error('Response not understood.')
                return
            if status and source == 'db':
                conn = sqlite3.connect(self.dbfilename)
                c = conn.cursor()
                c.execute('UPDATE contacts SET status=? WHERE email=?', (status, email))
                conn.commit()
                conn.close()
            i += 1
        print '[*] %d/%d targets pwned.' % (pwned, i)