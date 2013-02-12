import framework
# unique to module
import urllib
import re
import hashlib
import time
import random

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.classify = 'passive'
        self.info = {
                     'Name': 'Netcraft Hostname Enumerator',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Classification': '%s Reconnaissance' % (self.classify.title()),
                     'Description': 'Harvests hosts from Netcraft.com. This module updates the \'hosts\' table of the database with the results.',
                     'Comments': []
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.get_hosts()
    
    def get_hosts(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']
        url = 'http://searchdns.netcraft.com/'        
        payload = {'restriction': 'site+ends+with', 'host': domain}
        pattern = '<td align\=\"left\">\s*<a href=\"http://(.*?)/"'
        subs = []
        cnt = 0
        cookies = {}
        # control variables
        New = True
        # execute search engine queries and scrape results storing subdomains in a list
        # loop until no Next Page is available
        while New:
            content = None
            if verbose: self.output('URL: %s?%s' % (url, urllib.urlencode(payload)))

	    try: content = self.request(url, payload=payload, cookies=cookies)
	    except KeyboardInterrupt:
		print ''
	    except Exception as e:
		self.error(e.__str__())
	    if not content: break
	    
	    if 'set-cookie' in content.headers:
		# we have a cookie to set!
		cookie = content.headers['set-cookie']
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
		try: content = self.request(url, payload=payload, cookies=cookies)
		except KeyboardInterrupt:
		    print ''
		except Exception as e:
		    self.error(e.__str__())

            content = content.text

            sites = re.findall(pattern, content)
            # create a unique list
            sites = list(set(sites))
            
            # add subdomain to list if not already exists
            for site in sites:
                if site not in subs:
                    subs.append(site)
                    self.output('%s' % (site))
                    cnt += self.add_host(site)
            
            # Verifies if there's more pages to look while grabbing the correct 
            # values for our payload...
            link = re.findall(r'(\blast\=\b|\bfrom\=\b)(.*?)&', content)
            if not link:
                New = False
                break
            else:
                payload['last'] = link[0][1]
                payload['from'] = link[1][1]
                if verbose: self.output('Next page available! Requesting again...' )
		# sleep script to avoid lock-out
		if verbose: self.output('Sleeping to Avoid Lock-out...')
		try: time.sleep(random.randint(5,15))
		except KeyboardInterrupt:
		    print ''
		    break

        if verbose: self.output('Final Query String: %s?%s' % (url, urllib.urlencode(payload)))
        self.output('%d total hosts found.' % (len(subs)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))
