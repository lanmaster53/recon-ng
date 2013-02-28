import framework
# unique to module
import pwnedlist

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.info = {
                     'Name': 'PwnedList - Leak Details Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for information associated with all known leaks and stores them in the database.',
                     'Comments': [
                                  'API Query Cost: 1 query per request.'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.leak_dump()

    def leak_dump(self):
        # api key management
        key = self.manage_key('pwned_key', 'PwnedList API Key').encode('ascii')
        if not key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret').encode('ascii')
        if not secret: return

        # API query guard
        if not pwnedlist.guard(1): return

        # delete leaks table
        self.query('DROP TABLE IF EXISTS leaks')
        self.output('Old \'leaks\' table removed from the database.')

        # setup API call
        method = 'leaks.info'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {}
        payload = pwnedlist.build_payload(payload, method, key, secret)
        # make request
        try: resp = self.request(url, payload=payload)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        if resp.json:
            jsonobj = resp.json
        else:
            self.error('Invalid JSON returned from the API.')
            return

        # add leaks table
        columns = []
        values = []
        for key in jsonobj['leaks'][0].keys():
            columns.append('%s text' % (key))
        self.query('CREATE TABLE IF NOT EXISTS leaks (%s)' % (', '.join(columns)))
        self.output('New \'leaks\' table created.')

        # populate leaks table
        for leak in jsonobj['leaks']:
            self.insert('leaks', leak, leak.keys())
        self.output('%d leaks added to the \'leaks\' table.' % (len(jsonobj['leaks'])))
