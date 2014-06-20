import module
# unique to module
import re
import time
import urllib

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('username', 'lanmaster53', 'yes', 'username to validate')
        self.info = {
                     'Name': 'Dev Diver Repository Activity Examiner',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Searches public code repositories for information about a given username.',
                     }

    # Add a method for each repository
    def github(self, username):
        self.verbose('Checking Github...')
        url = 'https://github.com/%s' % (username)
        resp = self.request(url)
        gitUser = re.search('<span class="vcard-username" itemprop="additionalName">(.+?)</span>', resp.text)
        if gitUser:
            self.alert('Github username found - (%s)' % url)
            # extract data
            gitName = re.search('<span class="vcard-fullname" itemprop="name">(.+?)</span>', resp.text)
            gitDesc = re.search('<meta name="description" content="(.+)" />', resp.text)
            gitJoin = re.search('<span class="join-date">(.+?)</span>', resp.text)
            gitLoc = re.search('<span class="octicon octicon-location"></span>(.+?)</li>', resp.text)
            gitPersonalUrl = re.search('<span class="octicon octicon-link"></span><a href="(.+?)" class="url"', resp.text)
            # establish non-match values
            gitName = gitName.group(1) if gitName else None
            gitDesc = gitDesc.group(1) if gitDesc else None
            gitJoin = gitJoin.group(1) if gitJoin else None
            gitLoc = gitLoc.group(1) if gitLoc else None
            gitPersonalUrl = gitPersonalUrl.group(1) if gitPersonalUrl else None
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'Github'])
            tdata.append(['Name', gitName])
            tdata.append(['Profile URL', url])
            tdata.append(['Description', gitDesc])
            tdata.append(['Joined', time.strftime('%Y-%m-%d', time.strptime(gitJoin, '%b %d, %Y'))])
            tdata.append(['Location', gitLoc])
            tdata.append(['Personal URL', gitPersonalUrl])
            self.table(tdata, title='Github', store=False)
            # add the pertinent information to the database
            if gitName and len(gitName.split()) == 2:
                fname, lname = gitName.split()
                pass#self.add_contacts(fname, lname, 'Github account')
            else:
                pass#self.add_contacts(None, gitName, 'Github account')
        else:
            self.output('Github username not found.')

    def bitbucket(self, username):
        self.verbose('Checking Bitbucket...')
        # Bitbucket usernames are case sensitive, or at least will do a redirect if not using correct case
        # First we just use the username entered by the recon-ng user
        url = 'https://bitbucket.org/%s' % (username)
        resp = self.request(url)
        bbName = re.search('<title>\s+(.+) &mdash', resp.text)
        if not bbName:
            # Before we give up on the user not being on Bitbucket, let's search
            urlSearch = 'https://bitbucket.org/repo/all?name=%s' % (username)
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
            # extract data
            bbJoin = re.search('Member since <time datetime="(.+)T', resp.text)
            bbRepositories = re.findall('repo-link".+">(.+)</a></h1>', resp.text)
            # establish non-match values
            bbName = bbName.group(1)
            bbJoin = bbJoin.group(1) if bbJoin else None
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'Bitbucket'])
            tdata.append(['Name', bbName])
            tdata.append(['Profile URL', url])
            tdata.append(['Joined', bbJoin])
            for bbRepos in bbRepositories:
                tdata.append(['Repository', bbRepos])
            self.table(tdata, title='Bitbucket', store=False)
            # add the pertinent information to the database
            if len(bbName.split()) == 2:
                fname, lname = bbName.split()
                pass#self.add_contacts(fname, lname, 'Bitbucket account')
            else:
                pass#self.add_contacts(None, bbName, 'Bitbucket account')
        else:
            self.output('Bitbucket username not found.')

    def sourceforge(self, username):
        self.verbose('Checking SourceForge...')
        url = 'http://sourceforge.net/u/%s/profile/' % (username)
        resp = self.request(url)
        sfName = re.search('<title>(.+) / Profile', resp.text)
        print sfName
        if sfName:
            self.alert('Sourceforge username found - (%s)' % url)
            # extract data
            sfJoin = re.search('<dt>Joined:</dt><dd>\s*(\d\d\d\d-\d\d-\d\d) ', resp.text)
            sfLocation = re.search('<dt>Location:</dt><dd>\s*(\w.*)', resp.text)
            sfGender = re.search('<dt>Gender:</dt><dd>\s*(\w.*)', resp.text)
            sfProjects = re.findall('<a href="/p/.+/">(.+)</a>', resp.text)
            # establish non-match values
            sfName = sfName.group(1)
            sfJoin = sfJoin.group(1) if sfJoin else None
            sfLocation = sfLocation.group(1) if sfLocation else None
            sfGender = sfGender.group(1) if sfGender else None
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'Sourceforge'])
            tdata.append(['Name', sfName])
            tdata.append(['Profile URL', url])
            tdata.append(['Joined', sfJoin])
            tdata.append(['Location', sfLocation])
            tdata.append(['Gender', sfGender])
            for sfProj in sfProjects:
                tdata.append(['Projects', sfProj])
            self.table(tdata, title='Sourceforge', store=False)
            # add the pertinent information to the database
            if len(sfName.split()) == 2:
                fname, lname = sfName.split()
                pass#self.add_contacts(fname, lname, 'Sourceforge account')
            else:
                pass#self.add_contacts(None, sfName, 'Sourceforge account')
        else:
            self.output('Sourceforge username not found.')

    def codeplex(self, username):
        self.verbose('Checking CodePlex...')
        url = 'http://www.codeplex.com/site/users/view/%s' % (username)
        resp = self.request(url)
        cpName = re.search('<h1 class="user_name" style="display: inline">(.+)</h1>', resp.text)
        if cpName:
            self.alert('CodePlex username found - (%s)' % url)
            # extract data
            cpJoin = re.search('Member Since<span class="user_float">([A-Z].+[0-9])</span>', resp.text)
            cpLast = re.search('Last Visit<span class="user_float">([A-Z].+[0-9])</span>', resp.text)
            cpCoordinator = re.search('(?s)<p class="OverflowHidden">(.*?)</p>', resp.text)
            # establish non-match values
            cpName = cpName.group(1)
            cpJoin = cpJoin.group(1) if cpJoin else None
            cpLast = cpLast.group(1) if cpLast else None
            cpCoordinator = cpCoordinator.group(1) if cpCoordinator else None
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'CodePlex'])
            tdata.append(['Name', cpName])
            tdata.append(['Profile URL', url])
            tdata.append(['Joined', time.strftime('%Y-%m-%d', time.strptime(cpJoin, '%B %d, %Y'))])
            tdata.append(['Date Last', time.strftime('%Y-%m-%d', time.strptime(cpLast, '%B %d, %Y'))])
            cpCoordProject = re.findall('<a href="(http://.+)/" title=".+">(.+)<br /></a>', cpCoordinator)
            for cpReposUrl, cpRepos in cpCoordProject:
                tdata.append(['Project', '%s (%s)' % (cpRepos, cpReposUrl)])
            self.table(tdata, title='CodePlex', store=False)
            # add the pertinent information to the database
            if len(cpName.split()) == 2:
                fname, lname = cpName.split()
                pass#self.add_contacts(fname, lname, 'CodePlex account')
            else:
                pass#self.add_contacts(None, cpName, 'CodePlex account')
        else:
            self.output('CodePlex username not found.')

    def freecode(self, username):
        self.verbose('Checking Freecode...')
        url = 'http://freecode.com/users/%s' % (username)
        resp = self.request(url)
        fcCreated = re.search('(?s)<dt>Created</dt>.+?<dd>(\d\d.+:\d\d)</dd>', resp.text)
        if fcCreated:
            self.alert('Freecode username found - (%s)' % url)
            # extract data
            fcRepositories = re.findall('<a href="/projects/[^"]*" title="[^"]*">([^<]*)</a>', resp.text)
            # establish non-match values
            fcCreated = fcCreated.group(1) if fcCreated else None
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'Freecode'])
            tdata.append(['Profile URL', url])
            tdata.append(['Created', time.strftime('%Y-%m-%d', time.strptime(fcCreated, '%d %b %Y %H:%M'))])
            for fcProjName in fcRepositories:
                tdata.append(['Project', fcProjName])
            self.table(tdata, title='Freecode', store=False)
            # add the pertinent information to the database
        else:
            self.output('Freecode username not found.')

    def gitorious(self, username):
        self.verbose('Checking Gitorious...')
        url = 'https://gitorious.org/~%s' % (username)
        resp = self.request(url)
        if re.search('href="/~%s" class="avatar"' % (username), resp.text):
            self.alert('Gitorious username found - (%s)' % url)
            # extract data
            gitoName = re.search('<strong>([^<]*)</strong>\s+</li>\s+<li class="email">', resp.text)
            # Gitorious URL encodes the user's email to obscure it...lulz. No problem.
            gitoEmailRaw = re.search("eval\(decodeURIComponent\('(.+)'", resp.text)
            gitoEmail = re.search(r'mailto:([^\\]+)', urllib.unquote(gitoEmailRaw.group(1))) if gitoEmailRaw else None
            gitoJoin = re.search('Member for (.+)', resp.text)
            gitoPersonalUrl = re.search('rel="me" href="(.+)">', resp.text)
            gitoProjects = re.findall('<tr class="project">\s+<td>\s+<a href="/([^"]*)">([^<]*)</a>\s+</td>\s+</tr>', resp.text)
            # establish non-match values
            gitoName = gitoName.group(1) if gitoName else None
            gitoEmail = gitoEmail.group(1) if gitoEmail else None
            gitoJoin = gitoJoin.group(1) if gitoJoin else None
            gitoPersonalUrl = gitoPersonalUrl.group(1) if gitoPersonalUrl else None
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'Gitorious'])
            tdata.append(['Name', gitoName])
            tdata.append(['Profile URL', url])
            tdata.append(['Membership', gitoJoin])
            tdata.append(['Email', gitoEmail])
            tdata.append(['Personal URL', gitoPersonalUrl])
            for gitoProjUrl, gitoProjName in gitoProjects:
                tdata.append(['Project', '%s (https://gitorious.org/%s)' % (gitoProjName, gitoProjUrl)])
            self.table(tdata, title='Gitorious', store=False)
            # add the pertinent information to the database
            if gitoName and len(gitoName.split()) == 2:
                fname, lname = gitoName.split()
                pass#self.add_contacts(fname, lname, 'Gitorious account', gitoEmail)
            else:
                pass#self.add_contacts(None, gitoName, 'Gitorious account', gitoEmail)
        else:
            self.output('Gitorious username not found.')

    def module_run(self):
        username = self.options['username']

        # Check each repository
        self.github(username)
        self.bitbucket(username)
        self.sourceforge(username)
        self.codeplex(username)
        self.freecode(username)
        self.gitorious(username)
