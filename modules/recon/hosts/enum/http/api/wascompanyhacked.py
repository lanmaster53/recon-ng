import framework
# unique to module
import re
import datetime

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('company', self.goptions['company']['value'], 'yes', self.goptions['company']['desc'])
        self.register_option('hashtags', '#xss #sqli #breached #hacked #pwnd', 'yes', 'list of hashtags to search for')
        self.info = {
                     'Name': 'WasCompanyHacked Twitter Search',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches Twitter for breach related hashtags appearing with the given company name.',
                     'Comments': [
                                  'Inspired by Lenny Zeltser\'s (@lennyzeltser) wascompanyhacked.com.'
                                  ]
                     }
    def module_run(self):
        company = self.options['company']['value']
        hashtags = self.options['hashtags']['value']

        hashtags = ' OR '.join([x for x in re.split(',| ', hashtags) if x])
        query = '%s %s' % (hashtags, company)
        url = 'http://search.twitter.com/search.json'
        payload = {'q': query, 'rpp': 100, 'include_entities': 'true', 'result_type': 'mixed'}
        resp = self.request(url, payload=payload)
        jsonobj = resp.json
        tdata = []
        for result in jsonobj['results']:
            user = '@' + result['from_user']
            date = result['created_at']
            date = datetime.datetime.strptime(' '.join(date.split()[:-1]), '%a, %d %b %Y %H:%M:%S')
            date = datetime.datetime.strftime(date, '%d %b %Y')
            text = ' '.join(result['text'].split())
            tdata.append([user, date, text])
        if tdata:
            tdata.insert(0, ['From', 'Date', 'Text'])
            self.table(tdata, header=True)
        else:
            self.output('No results found.')
