import framework
# unique to module
from xml.dom.minidom import parseString

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'type': 'MD5',
                        'hash': '21232f297a57a5a743894a0e4a801fc3'
                        }
        self.info = {
                     'Name': 'MD5 Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses web based databases to perform a lookup of the given MD5 hash.',
                     'Comments': [
                                  'Type options: MD5'
                                  ]
                     }

    def do_run(self, params):
        self.lookup_hash()
    
    def lookup_hash(self):
        type = self.options['type'].lower()
        hash = self.options['hash']
        # lookup MD5 type hashes
        if type == 'md5':
            url = 'http://md5.noisette.ch/md5.php'
            payload = {'hash': hash}
            try: resp = self.request(url, payload=payload)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return
            dom = parseString(resp.text)
            try:
                cracked = dom.getElementsByTagName('string')[0].firstChild.wholeText
                self.alert('%s => %s' % (hash, cracked))
            except IndexError:
                error = dom.getElementsByTagName('error')[0].firstChild.wholeText
                if 'No value' in error:
                    self.output(error)
                else:
                    self.error(error)