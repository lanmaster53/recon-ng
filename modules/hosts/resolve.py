import _cmd
# unique to module
import sqlite3
import socket

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'verbose': False,
                        }

    def do_info(self, params):
        print 'Resolve module information.'

    def do_run(self, params):
        verbose = self.options['verbose']
        conn = sqlite3.connect(self.dbfilename)
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
            print '[Address] %s resolves to %s' % (host, address)
            c.execute('UPDATE hosts SET address=? WHERE rowid=?', (address, row))
        conn.commit()
        conn.close()