import _cmd
import __builtin__
# unique to module
import os
import urllib2
import urllib
import re

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'source': 'database'
                        }
        self.info = {
                     'Name': 'PwnedList Validator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages PwnedList.com to determine if email addresses are associated with breached credentials, updating the database with the results.',
                     'Comments': [
                                  'Source options: database, email@address, path/to/infile'
                                  ]
                     }

    def do_run(self, params):
        self.check_pwned()

    def check_pwned(self):
        verbose = self.goptions['verbose']
        source = self.options['source']

        # handle sources
        if source == 'database':
            emails = [x[0] for x in self.query('SELECT DISTINCT email FROM contacts WHERE email != "" ORDER BY email')]
            if len(emails) == 0:
                self.error('No email addresses in the database.')
                return
        elif '@' in source: emails = [source]
        elif os.path.exists(source): emails = open(source).read().split()
        else:
            self.error('Invalid source: %s' % (source))
            return

        # retrieve status
        pattern = "class='query_result_footer'>... we found your email in our database a total of (\d+?) times. It was last seen on ([\d-]+?). Please read on. <div"
        i, pwned = 0, 0
        while i < len(emails):
            status = None
            email = emails[i].encode('utf-8')
            url = 'http://pwnedlist.com/query'
            values = {'query_input' : email,
                      'query_input_hash' : 'empty',
                      'submit' : 'CHECK' }
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data)
            try: response = self.urlopen(req)
            except KeyboardInterrupt:
                print ''
                break
            except urllib2.HTTPError as e: response = e
            except Exception as e:
                try: self.error('Error: %s. Retrying %s.' % (e.reason, email))
                except:
                    self.error('Unknown Error.')
                    return
                continue
            the_page = response.read()
            if 'Gotcha!' in the_page:
                self.error('Hm... Got a captcha.')
                return
            elif '>NOPE!<' in the_page:
                status = 'safe'
                if verbose: self.output('%s => %s.' % (email, status))
            elif '>YES<' in the_page:
                status = 'pwned'
                m = re.search(pattern, the_page)
                qty = m.group(1)
                last = m.group(2)
                self.alert('%s => %s! Seen %s times as recent as %s.' % (email, status, qty, last))
                pwned += 1
            else:
                self.error('Response not understood.')
                return
            #if status and source == 'database':
            self.query('UPDATE contacts SET status="%s" WHERE email="%s"' % (status, email))
            i += 1
        self.output('%d/%d targets pwned.' % (pwned, i))