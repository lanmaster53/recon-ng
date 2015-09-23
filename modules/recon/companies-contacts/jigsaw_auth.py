from recon.core.module import BaseModule
from cookielib import CookieJar
import re
import math
import time
import urllib

class Module(BaseModule):

    meta = {
        'name': 'Jigsaw Authenticated Contact Enumerator',
        'author': 'Travis Lee (@eelsivart)',
        'description': 'Harvests contacts from Data.com using an authenticated user account. Updates the \'contacts\' table with the results. Use \'keys\' to set your jigsaw username and password before use.',
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL',
    }

    cookiejar = CookieJar()

    def module_run(self, companies):
        host = 'https://connect.data.com/company/view/'
        if self.perform_login():
            for company in companies:
                self.heading(company, level=0)
                comp, guid = self.get_company_url(company)
                if guid:
                    self.output('Gathering contacts for: %s' % comp)
                    self.get_contacts(host + guid)

    def perform_login(self):
        self.verbose('Authenticating to Data.com...')
        username = self.get_key('jigsaw_username')
        password = self.get_key('jigsaw_password')
        loginURL = 'https://connect.data.com/loginProcess'
        # perform login
        loginPayload = {'j_username': username, 'j_password': password, '_spring_security_remember_me': 'on'}
        resp = self.request(loginURL, method='POST', payload=loginPayload, cookiejar=self.cookiejar)
        if 'https://connect.data.com/login?' in resp.url:
            self.error('Login failed!')
            return False
        else:
            return True

    def get_company_url(self, companyName):
        companyURL = 'https://connect.data.com/dwr/call/plaincall/SearchDWR.findCompanies.dwr'
        respStr = ""
        # loop through all pages of results and add resp.text to a single var
        while True:
            companyPayload = {
                'callCount': 1,
                'windowName': 'DDC:us:search:Search',
                'c0-scriptName': 'SearchDWR',
                'c0-methodName': 'findCompanies',
                'c0-id': 0,
                'c0-param0': 'string:%s' % urllib.quote('{"filters":{"companies":["%s"]},"actionsOnColumns":{"activeContacts":{"sort":"desc"}},"totalRecordsOnPage":200}' % (companyName)),
                'batchId': 0,
                'instanceId': 0,
                'page': '%2Fsearch',
                'scriptSessionId': 'nOLcJJAzHyhfhym4Uf6dLsCdBRk/lXHdBR'
            }
            resp = self.request(companyURL, method='POST', payload=companyPayload, cookiejar=self.cookiejar)
            respStr = respStr + resp.text
            nameCheck = re.findall('e,name:"(.*?)",state:', resp.text, re.DOTALL)
            # perform some error checking on the response
            errCheck = self.validate_response(resp)
            if errCheck is 'error':
                return None, None
            elif errCheck is 'loggedin':
                continue
            break
        # process the company results
        companies = []
        guids = []
        tags_name = re.findall('e,name:"(.*?)",state:', respStr, re.DOTALL)
        tags_guid = re.findall(',guid:"(.*?)",hqPhone:', respStr, re.DOTALL)
        # build companies and guids list
        for tag, guid in zip(tags_name, tags_guid):
            companies.append(tag)
            guids.append(guid)
        # return nothing if there are no matches
        if not companies:
            self.output('No company matches found.')
        # return a unique match in such exists
        elif len(companies) == 1:
            self.alert('Unique company match found: %s' % (companies[0]))
            return (companies[0], guids[0])
        # prompt the user to choose from multiple matches
        else:
            # display the choices
            choices = range(0, len(companies))
            for i in choices:
                self.output('[%d] %s' % (i, companies[i]))
            choice = raw_input('Choose a company [0]: ')
            # the first choice is the default
            if choice is '':
                return (companies[0], guids[0])
            # make sure the choice is valid
            elif choice not in [str(x) for x in choices]:
                self.output('Invalid choice.')
            # return the chosen company and guid
            else:
                return (companies[int(choice)], guids[int(choice)])
        return None, None

    def get_contacts(self, url):
        page = 1
        while True:
            # request to company page url
            resp = self.request(url, cookiejar=self.cookiejar)
            # perform some error checking on the response
            errCheck = self.validate_response(resp)
            if errCheck is 'error':
                break
            elif errCheck is 'loggedin':
                continue
            # if company page has been merged to another page
            if 'This company has been merged into' in resp.text:
                self.verbose('Company merged. Switching...')
                newURLPath = re.findall('This company has been merged into <a href="(.*?)">', resp.text, re.DOTALL)
                url = "https://connect.data.com" + newURLPath[0]
                resp = self.request(url, cookiejar=self.cookiejar)
            else:
                companyName = re.findall('<div class="company-info-title">(.*?)</div>', resp.text, re.DOTALL)
                companyWebsite = re.findall('<td class="form-section-label">Website</td>\s*<td class="company-info-data"><a href="[^"]*" target="_blank">([^<]*)</a></td>', resp.text, re.DOTALL)
                contactsURL = 'https://connect.data.com/dwr/call/plaincall/SearchDWR.findContacts.dwr'
                contactsPayload = {
                    'callCount': 1,
                    'windowName': 'DDC:us:search:Search',
                    'c0-scriptName': 'SearchDWR',
                    'c0-methodName': 'findContacts',
                    'c0-id': 0,
                    'c0-param0': 'string:%s' % urllib.quote('{"filters":{"companies":["%s"]},"actionsOnColumns":{"companyName":{"sort":"asc"}},"currentPage":%d,"totalRecordsOnPage":200}' % (companyWebsite[0], page)),
                    'batchId': 0,
                    'instanceId': 0,
                    'page': '%2Fsearch',
                    'scriptSessionId': '=blAwiRVKg'
                }
                # request to extract contacts using bot mitigation cookie and sessionid
                resp = self.request(contactsURL, method='POST', payload=contactsPayload, cookiejar=self.cookiejar)
                if not "resultList:[],totalCount:" in resp.text:
                    # parse contacts
                    names = re.findall('e,name:"(.*?)",owned:', resp.text, re.DOTALL)
                    titles = re.findall('",title:"(.*?)",updated:', resp.text, re.DOTALL)
                    cities = re.findall(',city:"(.*?)",company:', resp.text, re.DOTALL)
                    states = re.findall(',state:"(.*?)",title:', resp.text, re.DOTALL)
                    countries = re.findall(',country:"(.*?)",directDial:', resp.text, re.DOTALL)
                    for name, title, city, state, country in zip(names, titles, cities, states, countries):
                        lname, mname, fname = self.parse_name(name)
                        region = city + ", " + state
                        self.output('%s - %s (%s)' % (name, title, region))
                        self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=title, region=region, country=country)
                    # break out of loop if results list is less than 200 as that is the last page
                    if len(names) < 200:
                        break
                    else:
                        page += 1
                        self.delay(10)
                # break out of loop when there are no more results
                else:
                    break

    # pause for a lil bit between pages to prevent captcha
    def delay(self, secs):
        self.verbose('Pausing for a few seconds to prevent CAPTCHA...')
        time.sleep(secs)

    # perform some error checks on the response
    def validate_response(self, resp):
        if '{arguments:["blocked"],key:"captcha"}' in resp.text:
            self.error('Too many requests, the site is requiring a CAPTCHA. Please wait a little while before re-running.')
            return 'error'
        elif '/login?' in resp.url:
            self.error('Session no longer valid. Trying to login again...')
            if self.perform_login():
                return 'loggedin' # if login succeeds
            else:
                return 'error' # if login fails again
        else:
            return 'success'
