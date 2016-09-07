#
# BrundleFuzz server side database operations
# SQLite is beautiful
#

import sqlite3 as sqlite
import sys


class CrashDataBase(object):
    """
    Some convenience wrappers for the
    SQLite database operations
    """
    def __init__(self, parent):
        """
        Simplicity is better than complexity
        """
        self.parent = parent
        self.ae = parent.ae
        self.cfg = parent.cfg

        try:
            self.con = sqlite.connect('fuzz.db')
            self.cur = self.con.cursor()

            self.cur.executescript("""
                CREATE TABLE IF NOT EXISTS Crashes ( \
                Id INTEGER PRIMARY KEY, \
                NodeId TEXT, \
                Machine TEXT, \
                Cpu TEXT, \
                Victim TEXT, \
                EventName TEXT, \
                Ip TEXT, \
                Exploitable TEXT, \
                FileName TEXT);
                """)

            self.con.commit()

            self.ae.m_ok('Database initialized successfully :)')

        except sqlite.Error, e:
            if self.con:
                self.con.rollback()

            self.ae.m_fatal("Error: %s" % e.args[0])
            sys.exit(1)

    def write_crash(self, crash_properties):
        """
        Process data to a format suitable for
        storage in the SQLite database
        """
        node_id = crash_properties['node_id']
        machine = crash_properties['machine']
        cpu = crash_properties['cpu']
        victim_pathname = crash_properties['victim']
        event_name = crash_properties['event_name']
        ip = crash_properties['ip']
        exp = crash_properties['exploitability']
        filename = crash_properties['filename']

        victim_filename = victim_pathname.split('\\')[-1]
        self.cur.execute("INSERT INTO Crashes(NodeId, Machine, Cpu, Victim, EventName, Ip, Exploitable, FileName) \
                         VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');"
                         % (node_id, machine, cpu, victim_filename, event_name, ip, exp, filename))

        self.con.commit()

    def retrieve_crashes(self):
        """
        Gets all crash information
        :return: iterator of tuples
        """
        self.cur.execute("SELECT * FROM Crashes")
        rows = self.cur.fetchall()

        return rows
