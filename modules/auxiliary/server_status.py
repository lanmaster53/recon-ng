import _cmd
# unique to module
import urllib2

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {}
        self.info = {
                     'Name': 'Apache Server-Status Page Scanner',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Checks all of the hosts stored in the database for a \'server-status\' page.',
                     'Comments': [
                                  'http://blog.sucuri.net/2012/10/popular-sites-with-apache-server-status-enabled.html',
                                  'http://httpd.apache.org/docs/2.2/mod/mod_status.html',
                                  'Google dork: intitle:"Apache Status" inurl:"server-status"'
                                  ]
                     }

    def do_run(self, params):
        self.check_for_status()
    
    def check_for_status(self):
        hosts = self.query('SELECT host FROM hosts ORDER BY host')
        protocols = ['http', 'https']
        cnt = 0
        for host in hosts:
            for proto in protocols:
                url = '%s://%s/server-status/' % (proto, host[0])
                try: resp = self.urlopen(urllib2.Request(url))
                except KeyboardInterrupt:
                    print ''
                    code = None
                    break
                except urllib2.HTTPError as e:
                    code = e.code
                    continue
                except:
                    code = 'Error'
                    continue
                finally:
                    if self.goptions['verbose'] and code: self.output('%s => %s.' % (url, code))
                self.alert('%s => %s. Possible server status page found!' % (url, resp.code))
                cnt += 1
        self.output('%d Server Status pages found.' % (cnt))