import framework
# unique to module
import re
import time
import urllib

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('username', None, 'yes', 'username to validate')
        self.info = {
                     'Name': 'Dev Diver Repository Activity Examiner',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'This module takes a username and searches common, public code repositories for information about that username.',
                     'Comments': []
                     }
                     
    # Add a method for each repository                 
    def github(self, username):
        self.verbose('Checking Github...')
        url = 'https://github.com/%s' % username
        resp = self.request(url)
        gitName = re.search('<span class="vcard-fullname" itemprop="name">(.+?)</span>', resp.text)
        if gitName:
            self.alert('Github username found - (%s)' % url)
            gitDesc = re.search('<meta name="description" content="(.+)" />', resp.text)
            gitJoin = re.search('<span class="join-date">(.+?)</span>', resp.text)
            gitLoc = re.search('<span class="octicon octicon-location"></span>(.+?)</li>', resp.text)
            gitPersonalUrl = re.search('<span class="octicon octicon-link"></span><a href="(.+?)" class="url"', resp.text)
            gitAvatar = re.search('<img class="avatar" height="220" src="(.+?)"', resp.text)
            self.name.append([gitName.group(1), 'Github'])
            self.urlRepos.append([url, 'Github'])
            if gitJoin: 
                self.dateJoin.append([time.strftime('%Y-%m-%d', time.strptime(gitJoin.group(1), '%b %d, %Y')), 'Github'])
            if gitLoc: self.other.append(['Location', gitLoc.group(1), 'Github'])
            if gitDesc: self.other.append(['Description', gitDesc.group(1), 'Github'])
            if gitPersonalUrl: self.urlPersonal.append([gitPersonalUrl.group(1), 'Github'])
            if gitAvatar: self.urlAvatar.append([gitAvatar.group(1), 'Github'])
            if ' ' in gitName.group(1):
            	fname, lname = gitName.group(1).split(' ')
            	self.add_contact(fname, lname, None, None, None, None)
        else:
            self.output('Github username not found.')
    
    def bitbucket(self, username):
        self.verbose('Checking Bitbucket...')
        # Bitbucket usernames are case sensitive, or at least will do a redirect if not using correct case
        # First we just use the username entered by the recon-ng user
        url = 'https://bitbucket.org/%s' % username
        resp = self.request(url)
        bbName = re.search('<h1 title="Username:.+">(.+)</h1>', resp.text)      
        if not bbName:
            # Before we give up on the user not being on Bitbucket, let's search
            urlSearch = 'https://bitbucket.org/repo/all?name=%s' % username
            respSearch = self.request(url)
            bbUserName = re.search('<a class="repo-link" href="/(.+)/', respSearch.text)
            if bbUserName:
                url = 'https://bitbucket.org/%s' % bbUserName
                resp = self.request(url)            
                # At least one repository found. Capture username case
                bbName = re.search('<h1 title="Username:.+">(.+)</h1>', resp.text)
                
        # If there is a user there, get info about their account
        if bbName:
            self.alert('Bitbucket username found - (%s)' % url)
            bbJoin = re.search('Member since <time datetime="(.+)T', resp.text)
            bbReposCount = re.search('<span class="count">([0-9]+)</span> Repositories', resp.text)
            bbFollowerCount = re.search('<span class="count">([0-9]+)</span> Followers', resp.text)
            bbFollowingCount = re.search('<span class="count">([0-9]+)</span> Following', resp.text)
            bbRepositories = re.findall('repo-link".+">(.+)</a></h1>', resp.text)
            self.name.append([bbName.group(1), 'Bitbucket'])
            self.urlRepos.append([url, 'Bitbucket'])
            if bbJoin: self.dateJoin.append([bbJoin.group(1), 'Bitbucket'])
            if bbRepositories: self.repositories.append([', '.join(bbRepositories), 'Bitbucket'])
 	    if ' ' in bbName.group(1):
            	fname, lname = bbName.group(1).split(' ')
                self.add_contact(fname, lname, None, None, None, None)
        else:
            self.output('Bitbucket username not found.')
        
    def sourceforge(self, username):
        self.verbose('Checking SourceForge...')
        url = 'http://sourceforge.net/users/%s' % username
        resp = self.request(url)
        sfName = re.search('<label>Public Name:</label> (.+) </li>', resp.text)
        if sfName: 
            self.alert('Sourceforge username found - (%s)' % url)
            sfJoin = re.search('<label>Joined:</label> (\d\d\d\d-\d\d-\d\d) ', resp.text)
            sfRepositories = re.findall('<li class="item"><a href="/projects/.+>(.+)</a>', resp.text)
            sfMyOpenID = re.search('(?s)<label>My OpenID:</label>.+?<a href="(.+?)"', resp.text)
            self.name.append([sfName.group(1), 'Sourceforge'])
            self.urlRepos.append([url, 'Sourceforge'])
            if sfJoin: self.dateJoin.append([sfJoin.group(1), 'Sourceforge'])
            if sfMyOpenID: self.other.append(['URL (Open ID)', sfMyOpenID.group(1), 'Sourceforge'])
            if sfRepositories: self.repositories.append([', '.join(sfRepositories), 'Sourceforge'])
 	    if ' ' in sfName.group(1):
            	fname, lname = sfName.group(1).split(' ')
                self.add_contact(fname, lname, None, None, None, None)
        else:
            self.output('Sourceforge username not found.')

    def codeplex(self, username):
        self.verbose('Checking CodePlex...')
        url = 'http://www.codeplex.com/site/users/view/%s' % username
        resp = self.request(url)
        cpName = re.search('<h1 class="user_name" style="display: inline">(.+)</h1>', resp.text)
        if cpName: 
            self.alert('CodePlex username found - (%s)' % url)
            cpJoin = re.search('Member Since<span class="user_float">([A-Z].+[0-9])</span>', resp.text)
            cpLast = re.search('Last Visit<span class="user_float">([A-Z].+[0-9])</span>', resp.text)
            cpCoordinator = re.search('(?s)<p class="OverflowHidden">(.*?)</p>', resp.text)
            self.urlRepos.append([url, 'CodePlex'])
            if cpJoin: 
                self.dateJoin.append([time.strftime('%Y-%m-%d', time.strptime(cpJoin.group(1), '%B %d, %Y')), 'CodePlex'])
            if cpLast: 
                self.other.append(['Date Last', time.strftime('%Y-%m-%d', time.strptime(cpLast.group(1), '%B %d, %Y')), 'CodePlex'])
            if cpCoordinator: 
                cpCoordProject = re.findall('<a href="(http://.+)/" title=".+">(.+)<br /></a>', cpCoordinator.group(1))
                cpReposOut = []
                for cpReposUrl, cpRepos in cpCoordProject:
                    self.repositories.append([cpRepos + ' (' + cpReposUrl + ')', 'CodePlex'])
        else:
            self.output('CodePlex username not found.')
        
    def freecode(self, username):
        self.verbose('Checking Freecode...')
        url = 'http://freecode.com/users/%s' % username
        resp = self.request(url)
        fcCreated = re.search('(?s)<dt>Created</dt>.+?<dd>(\d\d.+:\d\d)</dd>', resp.text)
        if fcCreated: 
            self.alert('Freecode username found - (%s)' % url)
            fcRepositories = re.findall("'Projects', 'Website', '(.+?)'", resp.text)
            self.urlRepos.append([url, 'Freecode'])
            self.dateJoin.append([time.strftime('%Y-%m-%d', time.strptime(fcCreated.group(1), '%d %b %Y %H:%M')), 'Freecode'])
            if fcRepositories: self.repositories.append([', '.join(fcRepositories), 'Freecode'])
        else:
            self.output('Freecode username not found.') 

    def gitorious(self, username):
        self.verbose('Checking Gitorious...')
        url = 'https://gitorious.org/~%s' % username
        resp = self.request(url)
        if re.search('href="/~' + username + '" class="avatar"', resp.text):
            self.alert('Gitorious username found - (%s)' % url)          
            gitoName = re.search('([A-Za-z0-9].+)\s+</li>\s+<li class="email">', resp.text)
            if gitoName: self.name.append([gitoName.group(1), 'Gitorious'])
            
            # Gitorious URL encodes the user's email to obscure it...lulz. No problem.
            gitoEmailraw = re.search("eval\(decodeURIComponent\('(.+)'", resp.text)
            gitoEmail = re.search('mailto:(.+)\\"', urllib.unquote(gitoEmailraw.group(1)))
            gitoJoin = re.search('Member for (.+)', resp.text)
            gitoPersonalUrl = re.search('rel="me" href="(.+)">', resp.text)
            gitoAvatar = re.search('<img alt="avatar" height="16" src="(https://secure.gravatar.com/avatar/.+?)&', resp.text)
            gitoProjects = re.findall('(?s)<li class="project">\s+<a href="/(.+?)">', resp.text)
            self.urlRepos.append([url, 'Gitorious'])
            if gitoJoin: self.dateJoin.append([gitoJoin.group(1), 'Gitorious'])
            if gitoEmail: self.other.append(['Email', gitoEmail.group(1).strip('\\'), 'Gitorious'])
            if gitoPersonalUrl: self.urlPersonal.append([gitoPersonalUrl.group(1), 'Gitorious'])
            if gitoAvatar: self.urlAvatar.append([gitoAvatar.group(1), 'Gitorious'])
            if gitoProjects: self.repositories.append([', '.join(gitoProjects), 'Gitorious'])
 	    if ' ' in gitoName.group(1):
            	fname, lname = gitoName.group(1).split(' ')
                self.add_contact(fname, lname, None, gitoEmail, None, None)
        else:
            self.output('Gitorious username not found.')          
    
    def build_table(self, content, heading):
        if heading == 'Other': # The Other dictionary has 3 cols not 2.
            for name, value, repos in content:
                self.tdata.append([name, value, repos])
        else:
            for value, repos in content:
                self.tdata.append([heading, value, repos])
            self.tdata.append(['  -----', '  -----', '  -----'])
            
    
    def module_run(self):
        username = self.options['username']
        # Dictionaries to store the scraped data
        self.name = []
        self.dateJoin = []
        self.urlRepos = []
        self.repositories = []
        self.urlAvatar = []
        self.urlPersonal = []
        self.other = []
        
        # Check each repository
        self.github(username)
        self.bitbucket(username)
        self.sourceforge(username)
        self.codeplex(username)
        self.freecode(username)
        self.gitorious(username)
        
        # Print Final Output Table
        if self.name or self.dateJoin:
            self.tdata = []
            self.tdata.append(['Parameter', 'Value', 'Site'])
            if self.name: self.build_table(self.name, 'Real Name')
            if self.dateJoin: self.build_table(sorted(self.dateJoin), 'Date Joined')
            if self.urlRepos: self.build_table(sorted(self.urlRepos), 'URL (Repository)')
            if self.repositories: self.build_table(sorted(self.repositories), 'Repositories)') 
            if self.urlAvatar: self.build_table(sorted(self.urlAvatar), 'URL (Avatar)')
            if self.urlPersonal: self.build_table(sorted(self.urlPersonal), 'URL (Personal)')
            if self.other: self.build_table(sorted(self.other), 'Other')
            
            self.table(self.tdata, True)
        else:
           self.error('%s not found at any repository.' % username)
