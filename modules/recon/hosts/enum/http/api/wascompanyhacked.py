import framework
# unique to module
import re
import datetime

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('company', self.global_options['company'], 'yes', self.global_options.description['company'])
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
        company = self.options['company']
        hashtags = self.options['hashtags']

        hashtags = ' OR '.join([x for x in re.split(',| ', hashtags) if x])
        query = '%s %s' % (hashtags, company)
        self.bearer_token = self.get_twitter_oauth_token()
        headers = {'Authorization': 'Bearer %s' % (self.bearer_token)}
        payload = {'q': query, 'count': 100, 'include_entities': 'false', 'result_type': 'mixed'}
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        resp = self.request(url, payload=payload, headers=headers)
        jsonobj = resp.json
        if 'errors' in jsonobj:
            for error in jsonobj['errors']:
                self.error(error['message'])
            return
        tdata = []
        for status in jsonobj['statuses']:
            user = '@' + status['user']['screen_name']
            date = status['created_at']
            date = datetime.datetime.strptime(date, '%a %b %d %H:%M:%S +0000 %Y')
            date = datetime.datetime.strftime(date, '%d %b %Y')
            text = ' '.join(status['text'].split())
            tdata.append([user, date, text])
        if tdata:
            tdata.insert(0, ['From', 'Date', 'Text'])
            self.table(tdata, header=True)
        else:
            self.output('No results found.')
