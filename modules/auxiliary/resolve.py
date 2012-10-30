import _cmd
# unique to module
import sqlite3
import socket

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {}

    def do_info(self, params):
        print ''
        print 'Resolves the IP address for all of the hosts stored in the database.'
        print ''

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
            #print '[Address] %s resolves to %s' % (host, ','.join(addresses))
            try: address = socket.gethostbyname(host)
            except socket.gaierror: address = 'no entry'
            print '[Address] %s => %s' % (host, address)
            c.execute('UPDATE hosts SET address=? WHERE rowid=?', (address, row))
        conn.commit()
        conn.close()