import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('username', None, 'yes', 'jigsaw account username')
        self.register_option('password', None, 'yes', 'jigsaw account password')
        self.info = {
                     'Name': 'Jigsaw - Point Usage Statistics Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the Jigsaw API for the point usage statistics of the given account.',
                     'Comments': []
                     }

    def module_run(self):
        username = self.options['username']['value']
        password = self.options['password']['value']
        key = self.manage_key('jigsaw_key', 'Jigsaw API Key')
        if not key: return

        url = 'https://www.jigsaw.com/rest/user.json'
        payload = {'token': key, 'username': username, 'password': password}
        try: resp = self.request(url, payload=payload, redirect=False)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        if resp.json: jsonobj = resp.json
        else:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return

        # handle output
        self.output('%d Jigsaw points remaining.' % (jsonobj['points']))
