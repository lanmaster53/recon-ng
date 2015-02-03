import module
# unique to module
from cookielib import CookieJar
import re
import urllib
import math

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT company FROM companies WHERE company IS NOT NULL ORDER BY company')
        self.info = {
            'Name': 'Jigsaw Contact Enumerator',
            'Description': 'Harvests contacts from Data.com. Updates the \'contacts\' table with the results.',
            'Comments': [
                'Discovery does not always succeed due to alphabetical inconsistencies in the Data.com data sets. Use \'https://connect.data.com/\' to drill down to the target company and set the \'SOURCE\' option as the URL.'
            ]
        }

    def module_run(self, companies):
        host = 'https://connect.data.com'
        for company in companies:
            if 'connect.data.com' in company.lower():
                self.get_contacts(company)
            else:
                self.heading(company, level=0)
                resource = self.get_company_url(host, company)
                if resource:
                    self.output('Gathering contacts...')
                    self.get_contacts(host + resource)

    def get_company_url(self, host, company):
        char = company[0].lower()
        char = char if char.isalpha() else '_'
        resource = '/directory/company/%s' % (char)
        while True:
            match = False
            # widdle down through the alphabetical list of companies
            url = host + resource
            self.verbose('Query: %s' % (url))
            resp = self.request(url)
            # check to see if companies have been reached
            if re.search('/directory/company/list', resp.text):
                return self.choose_company(resp, company)
            # keep widdling
            tags = re.findall('[^>]<a href="(/directory/company/[^"]*)">([^<]*)</a>', resp.text)
            # conduct an alphabetical comparison to determing which range to select
            for tag in tags:
                first = tag[1].split(' - ')[0].lower()
                last = tag[1].split(' - ')[1].lower()
                middle = company.lower()
                order = [first, middle, last]
                ordered = sorted(order)
                if middle in first or order == ordered:
                    match = True
                    resource = tag[0]
                    self.output('Alphabetical range identified: %s' % (tag[1]))
                    break
            # resource should equal tag[0] if range was found, otherwise return nothing
            if not match:
                self.output('Company not found in the provided alphabetical ranges.')
                return

    def choose_company(self, resp, company):
        companies = []
        tags = re.findall('<a href="(/directory/company/list/[^"]*)">([^<]*)</a>', resp.text)
        # build companies list of possible matches
        for tag in tags:
            if company.lower() in tag[1].lower():
                companies.append(tag)
        # return nothing if there are no matches
        if not companies:
            self.output('No company matches found.')
            return
        # return a unique match in such exists
        elif len(companies) == 1:
            self.alert('Unique company match found: %s' % (companies[0][1]))
            return companies[0][0]
        # prompt the user to choose from multiple matches
        else:
            # display the choices
            choices = range(0, len(companies))
            for i in choices:
                self.output('[%d] %s' % (i, companies[i][1]))
            choice = raw_input('Choose a company [0]: ')
            # the first choice is the default
            if choice is '':
                return companies[0][0]
            # make sure the choice is valid
            elif choice not in [str(x) for x in choices]:
                self.output('Invalid choice.')
                return
            # return the chosen company id
            else:
                return companies[int(choice)][0]

    def get_contacts(self, url):
        payload = {'page': 1}
        first = True
        cookiejar = CookieJar()
        while True:
            if first:
                first = False
                # request to fetch challenge
                resp = self.request(url, payload=payload, cookiejar=cookiejar)
                if 'Challenge=' in resp.text:
                    challengeid, challenge, answer = solve_challenge(resp.text)
                else:
                    self.verbose('No challenge found.')
                    continue
                headers = {
                    'X-AA-Challenge-ID': challengeid,
                    'X-AA-Challenge-Result': answer,
                    'X-AA-Challenge': challenge,
                    'Content-Type': 'text/plain',
                    'Referer': url+"?"+urllib.urlencode(payload),
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0'
                }
                # request to answer challenge and fetch bot mitigation cookie
                resp = self.request(url+"?"+urllib.urlencode(payload), method='POST', headers=headers, payload={}, cookiejar=cookiejar)
            # request to extract contacts using bot mitigation cookie
            resp = self.request(url, payload=payload, cookiejar=cookiejar)
            if 'Sorry. No contacts found for' in resp.text: break
            #if not re.search('\?page='): break
            values = re.findall('<td class="ellipsis">[^>]*>([^<]*)</span>', resp.text, re.DOTALL)
            contacts = [values[i:i+6] for i in range(0, len(values), 6)]
            for contact in contacts:
                fname = self.html_unescape(contact[1])
                # fname includes the preferred name as an element that needs to be removed
                fname = ' '.join(fname.split()[:2]) if len(fname.split()) > 2 else fname
                lname = self.html_unescape(contact[0])
                name = '%s %s' % (fname, lname)
                fname, mname, lname = self.parse_name(name)
                title = self.html_unescape(contact[2])
                loc1 = self.html_unescape(contact[5])
                loc2 = self.html_unescape('')
                region = []
                for item in [loc1, loc2]:
                    if item: region.append(item)
                region = ', '.join(region)
                self.output('%s - %s (%s)' % (name, title, region))
                self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=title, region=region)
            payload['page'] += 1

def solve_challenge(text):
    # parse challenge data
    challenge_re = re.findall('Challenge=[0-9]+', text)
    challengeid_re = re.findall('ChallengeId=[0-9]+', text)
    challenge = challenge_re[0].split('=')[1]
    challengeid = challengeid_re[0].split('=')[1]
    # solve challenge
    var_str = challenge
    var_arr = list(var_str)
    var_arr_rev = var_arr
    var_arr_rev.reverse()
    lastdig = var_arr_rev[0]
    var_arr_sorted = var_arr
    var_arr_sorted.sort()
    mindig = var_arr_sorted[0]
    subvar1 = (2 * int(var_arr[2]))+(int(var_arr[1])*1)
    subvar2 = str(2 * int(var_arr[2]))+""+var_arr[1]
    my_pow = int(math.pow(((int(var_arr[0])*1)+2),int(var_arr[1])))
    x = (int(challenge)*3+subvar1)*1
    y = int(math.cos(math.pi*int(subvar2)))
    answer = int(x)*int(y)
    answer -= my_pow*1
    answer += (int(mindig)*1)-(int(lastdig)*1)
    answer = str(answer)+""+str(subvar2)
    return challengeid, challenge, answer
