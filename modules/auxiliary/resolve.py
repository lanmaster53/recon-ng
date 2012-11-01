import _cmd
# unique to module
import sqlite3
import socket

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {}
        self.info = {
                     'Name': 'Hostname Resolver',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Resolves the IP address for all of the hosts stored in the database.',
                     'Comments': []
                     }

    def do_run(self, params):
        self.resolve_hosts()
    
    def resolve_hosts(self):
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        hosts = c.execute('SELECT rowid, host FROM hosts ORDER BY host').fetchall()
        for host in hosts:
            row = host[0]
            host = host[1]
            #try: addresses = list(set([item[4][0] for item in socket.getaddrinfo(host, 80)]))
            #except socket.gaierror: addresses = ['no entry']
            #self.output('%s resolves to %s' % (host, ','.join(addresses)))
            try: address = socket.gethostbyname(host)
            except socket.gaierror: address = 'no entry'
            self.output('%s => %s' % (host, address))
            c.execute('UPDATE hosts SET address=? WHERE rowid=?', (address, row))
        conn.commit()
        conn.close()