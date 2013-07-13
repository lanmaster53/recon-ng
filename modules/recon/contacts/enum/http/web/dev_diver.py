import framework
# unique to module
import re
import time
import urllib

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('username', None, 'yes', 'Username to validate')
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
        gitName = re.search('<span itemprop="\w*[nN]ame"[^>]*>(.+)</span>', resp.text)
        if gitName: 
            self.alert('Github username found - (%s)' % url)
            gitDesc = re.search('<meta name="description" content="(.+)" />', resp.text)
            gitJoin = re.search('<span class="join-date">(.+)</span>', resp.text)
            gitLoc = re.search('<dd itemprop="homeLocation">(.+)</dd>', resp.text)
            gitPersonalUrl = re.search('<dd itemprop="url"><a href="(.+?)" class="url"', resp.text)
            gitAvatar = re.search('<a href="(https://secure.gravatar.com/avatar/.+?)\?;', resp.text)
            self.tdata.append(['Real Name', 'Github', gitName.group(1)])
            self.tdata.append(['URL', 'Github', url])
            if gitJoin: 
                self.tdata.append(['Join Date', 'Github', time.strftime('%Y-%m-%d', time.strptime(gitJoin.group(1), '%b %d, %Y'))])
            if gitLoc: self.tdata.append(['Home Location', 'Github', gitLoc.group(1)])
            if gitDesc: self.tdata.append(['Description', 'Github', gitDesc.group(1)])
            if gitPersonalUrl: self.tdata.append(['URL (Personal)', 'Github', gitPersonalUrl.group(1)])
            if gitAvatar: self.tdata.append(['Avatar', 'Github', gitAvatar.group(1)])
        else:
            self.output('Github username not found')
    
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
            self.tdata.append(['Real Name', 'Bitbucket', bbName.group(1)])
            self.tdata.append(['URL', 'Bitbucket', url])
            if bbJoin: self.tdata.append(['Join Date', 'Bitbucket', bbJoin.group(1)])
            if bbFollowerCount and int(bbFollowerCount.group(1)) > 0: 
                self.tdata.append(['# of Followers', 'Bitbucket', bbFollowerCount.group(1)])
            if bbFollowingCount and int(bbFollowingCount.group(1)) > 0: 
                self.tdata.append(['# Projects Following', 'Bitbucket', bbFollowingCount.group(1)])
            if bbRepositories: self.tdata.append(['Repository Names', 'Bitbucket', ', '.join(bbRepositories)])
        else:
            self.output('Bitbucket username not found')
        
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
            self.tdata.append(['Real Name', 'Sourceforge', sfName.group(1)])
            self.tdata.append(['URL', 'Sourceforge', url])
            if sfJoin: self.tdata.append(['Join Date', 'Sourceforge', sfJoin.group(1)])
            if sfMyOpenID: self.tdata.append(['URL (Open ID)', 'Sourceforge', sfMyOpenID.group(1)])
            if sfRepositories: self.tdata.append(['Repository Names', 'Sourceforge', ', '.join(sfRepositories)])
        else:
            self.output('Sourceforge username not found')

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
            self.tdata.append(['URL', 'CodePlex', url])
            if cpJoin: 
                self.tdata.append(['Join Date', 'CodePlex', time.strftime('%Y-%m-%d', time.strptime(cpJoin.group(1), '%B %d, %Y'))])
            if cpLast: 
                self.tdata.append(['Last Date', 'CodePlex', time.strftime('%Y-%m-%d', time.strptime(cpLast.group(1), '%B %d, %Y'))])
            if cpCoordinator: 
                cpCoordProject = re.findall('<a href="(http://.+)/" title=".+">(.+)<br /></a>', cpCoordinator.group(1))
                cpReposOut = []
                for cpReposUrl, cpRepos in cpCoordProject:
                    self.tdata.append(['Coordinator for', 'CodePlex', cpRepos + ' (' + cpReposUrl + ')'])
        else:
            self.output('CodePlex username not found')
        
    def freecode(self, username):
        self.verbose('Checking Freecode...')
        url = 'http://freecode.com/users/%s' % username
        resp = self.request(url)
        fcCreated = re.search('(?s)<dt>Created</dt>.+?<dd>(\d\d.+:\d\d)</dd>', resp.text)
        if fcCreated: 
            self.alert('Freecode username found - (%s)' % url)
            fcRepositories = re.findall("'Projects', 'Website', '(.+?)'", resp.text)
            self.tdata.append(['URL', 'Freecode', url])
            self.tdata.append(['Join Date', 'Freecode', time.strftime('%Y-%m-%d', time.strptime(fcCreated.group(1), '%d %b %Y %H:%M'))])
            if fcRepositories: self.tdata.append(['Repository Names', 'Freecode', ', '.join(fcRepositories)])
        else:
            self.output('Freecode username not found') 

    def gitorious(self, username):
        self.verbose('Checking Gitorious...')
        url = 'https://gitorious.org/~%s' % username
        resp = self.request(url)
        if re.search('href="/~' + username + '" class="avatar"', resp.text):
            self.alert('Gitorious username found - (%s)' % url)          
            gitoName = re.search('([A-Za-z0-9].+)\s+</li>\s+<li class="email">', resp.text)
            if gitoName: self.tdata.append(['Real Name', 'Gitorious', gitoName.group(1)])
            
            # Gitorious URL encodes the user's email to obscure it...lulz. No problem.
            gitoEmailraw = re.search("eval\(decodeURIComponent\('(.+)'", resp.text)
            gitoEmail = re.search('mailto:(.+)\\"', urllib.unquote(gitoEmailraw.group(1)))
            gitoJoin = re.search('Member for (.+)', resp.text)
            gitoPersonalUrl = re.search('rel="me" href="(.+)">', resp.text)
            gitoAvatar = re.search('<img alt="avatar" height="16" src="(https://secure.gravatar.com/avatar/.+?)&', resp.text)
            gitoProjects = re.findall('(?s)<li class="project">\s+<a href="/(.+?)">', resp.text)
            self.tdata.append(['URL', 'Gitorious', url])
            if gitoJoin: self.tdata.append(['Join Date', 'Gitorious', gitoJoin.group(1)])
            if gitoEmail: self.tdata.append(['Email', 'Gitorious', gitoEmail.group(1).strip('\\')])
            if gitoPersonalUrl: self.tdata.append(['URL (Personal)', 'Gitorious', gitoPersonalUrl.group(1)])
            if gitoAvatar: self.tdata.append(['Avatar', 'Gitorious', gitoAvatar.group(1)])
            if gitoProjects: self.tdata.append(['Project Names', 'Gitorious', ', '.join(gitoProjects)])
        else:
            self.output('Gitorious username not found')          
    
    def module_run(self):
        username = self.options['username']['value']
        self.tdata = []
        
        # Check each repository
        self.github(username)
        self.bitbucket(username)
        self.sourceforge(username)
        self.codeplex(username)
        self.freecode(username)
        self.gitorious(username)

        # Print Final Output Table
        if len(self.tdata) > 1: 
            sortedTdata = sorted(self.tdata)
            sortedTdata.insert(0, ['Parameter', 'Site', 'Value'])
            self.table(sortedTdata, True)
        else:
            self.error('%s not found at any repository' % username)
