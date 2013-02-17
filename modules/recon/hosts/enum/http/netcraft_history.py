import framework
# unique to module
import re
import hashlib
import urllib
import time
import random

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Hosting History',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Description': 'Checks Netcraft for the Hosting History of given target.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]'
                                 ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.netcraft()

    def netcraft(self):
        verbose = self.options['verbose']['value']
        cookies = {}

        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return

        for host in hosts:
            url = 'http://uptime.netcraft.com/up/graph?site=%s' % (host)
            if verbose: self.output('URL: %s' % url)
            try: resp = self.request(url, cookies=cookies)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
            if not resp: break

            if 'set-cookie' in resp.headers:
                # we have a cookie to set!
                if verbose: self.output('Setting cookie...')
                cookie = resp.headers['set-cookie']
                # this was taken from the netcraft page's JavaScript, no need to use big parsers just for that
                # grab the cookie sent by the server, hash it and send the response
                challenge_token = (cookie.split('=')[1].split(';')[0])
                response = hashlib.sha1(urllib.unquote(challenge_token))
                cookies = {
                            'netcraft_js_verification_response': '%s' % response.hexdigest(),
                            'netcraft_js_verification_challenge': '%s' % challenge_token,
                            'path' : '/'
                          }

                # Now we can request the page again
                if verbose: self.output('URL: %s' % url)
                try: resp = self.request(url, cookies=cookies)
                except KeyboardInterrupt:
                    print ''
                except Exception as e:
                    self.error(e.__str__())
                if not resp: break

            content = resp.text

            # instantiate history list
            history = []
            rows = re.findall(r'<tr class="T\wtr\d*">(?:\s|.)+?<\/div>', content)
            for row in rows:
                cell = re.findall(r'>(.*?)<', row)
                raw  = [cell[0], cell[2], cell[4], cell[6], cell[8]]
                history.append([x.strip() for x in raw])

            if len(history) > 0:
                header = ['OS', 'Server', 'Last Changed', 'IP Address', 'Owner']
                history.insert(0, header)
                self.table(history, True)
            else:
                self.output('No results found')

            if len(hosts) > 1:
                # sleep script to avoid lock-out
                if verbose: self.output('Sleeping to Avoid Lock-out...')
                try: time.sleep(random.randint(5,15))
                except KeyboardInterrupt:
                    print ''
                    break
