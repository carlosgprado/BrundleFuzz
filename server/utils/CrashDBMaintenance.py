#
# Command Line Application to ease with 
# Crash database maintenance
#

import os
import sys
import sqlite3 as sqlite
import cmd


class CrashDBCmd(cmd.Cmd):
    """
    Simple command line processor example.
    Shelling out is implemented.
    """
    # These properties control the
    # graphical appearence
    last_output = ''
    ruler = '_'

    def banner(self):
        print '*' * 60
        print '* Crash Database Administration'
        print '* You can shell out with: !command'
        print '*' * 60
        print

    def do_prompt(self, line):
        """
        Change the interactive prompt
        """
        if line:
            self.prompt = "(%s) " %line

        else:
            print 'Please specify a prompt text'

    def do_shell(self, line):
        """
        Run a shell command
        """
        print 'Running shell command:', line
        output = os.popen(line).read()
        print output
        self.last_output = output

    def do_echo(self, line):
        """
        Print the input, replacing '$out' with the
        output of the last shell command
        """
        print line.replace('$out', self.last_output)

    def do_resetdb(self, line):
        """
        Clears the DB
        """
        self.db.empty_db()

    def do_print_records(self, exploitability):
        """
        Usage:
        print_records [exploitability]
        """
        self.db.print_records_like(exploitability)

    def do_insert_dummy_record(self, exploitability):
        """
        For testing purposes
        """
        self.db.insert_dummy_record(exploitability)

    def preloop(self):
        """
        Executed once before the Cmd prompt
        """
        self.banner()
        self.db = CrashDBConnector('fuzz.db')

    def postloop(self):
        """
        Executed once after the Cmd prompt
        """
        print 'Bye!'

    def precmd(self, line):
        """
        Executed once before each command
        This will print an additional blank line
        """
        return cmd.Cmd.precmd(self, line)

    def postcmd(self, stop, line):
        """
        Executed once after each command
        This will print an additional blank line
        """
        print
        return cmd.Cmd.postcmd(self, stop, line)

    def do_quit(self, line):
        """
        Quits the application, obviously
        """
        return True


class CrashDBConnector(object):
    def __init__(self, sqlite_file):
        print 'Initializing DB connector...'
        self.con = None
        self.cur = None
        self.file = sqlite_file

        self.connect_to_db()

    def connect_to_db(self):
        """
        Open a connection to the SQLite DB
        """
        try:
            self.con = sqlite.connect(self.file)
            self.cur = self.con.cursor()
            print 'Connected to', self.file
            print

        except sqlite.Error, e:
            if self.con:
                self.con.rollback()

            print 'Error connecting to', self.file
            print 'Exception follows:'
            print e
            print 'Quitting...'
            sys.exit(1)

    def empty_db(self):
        """
        Resets the database to its initial
        state (empty, in this case)
        """
        try:
            self.cur.execute("DELETE FROM Crashes;")
            self.con.commit()
            print 'Deleted all records'

        except sqlite.Error, e:
            print 'Unable to delete all records.'
            print 'Exception follows:'
            print e

    def insert_dummy_record(self, exploitability):
        """
        For testing purposes
        """
        if not exploitability:
            exploitability = 'Exploitable'
            
        try:
            query = "INSERT INTO Crashes(NodeId, Victim, Cpu, EventName, Ip, StackTrace, CrashLabel, Exploitable, FileName) VALUES('Win7', 'Test Victim', 'x86_64', 'Test Event', '10000', 'msvcrt!test+0x414141', 'Example Label', '%s', 'dummy.bmp');" % exploitability
            self.cur.execute(query)
            self.con.commit()
            print 'Inserted dummy record'

        except sqlite.Error, e:
            print 'Unable to insert dummy record'
            print 'Exception follows:'
            print e

    def print_records_like(self, exploitability):
        """
        Displays all records with a specific 
        exploitability probability
        """
        if not exploitability:
            query = "SELECT * FROM Crashes"

        else:
            query = "SELECT * FROM Crashes WHERE Exploitable = '%s';" % exploitability

        display_fmt = "%d %s %s %s %s 0x%x %s %s %s %s"

        try:
            self.cur.execute(query)
            rows = self.cur.fetchall()

            if not rows:
                if not exploitability:
                    print 'Could not find records with any exploitability level'

                else:
                    print 'Could not find records with exploitability:', exploitability

                return

            for row in rows:
                (idx, n, v, c, e, i, s, cl, ex, f) = row
                values = row[:5] + (int(i),) + row[6:]
                print display_fmt %values

        except sqlite.Error, e:
            print 'Unable to display records.'
            print 'Exception follows:'
            print e


if __name__ == '__main__':
    CrashDBCmd().cmdloop()
