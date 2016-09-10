#
# This is preliminary. It performs a
# dummy analysis before saving the
# offending file.
# TODO: implement some simple analysis
# with gdb or similar.
#

from time import time
from utils import Utils


class CrashAnalysis(object):
    def __init__(self, parent):
        self.file_info = None
        self.victim_filename = ''
        self.crash_filename = ''
        self.parent = parent
        self.ae = parent.ae
        self.cfg = parent.cfg
        self.fo = self.parent.fileops
        self.utils = Utils(self)

    def analyze_crash(self, cmd):
        """
        This is called with the command line (including the filename)
        which caused the crash before.
        It is a late analysis routine which sorts the crashes.
        """

        # TODO: This may not always be the case
        self.victim_filename, self.crash_filename = cmd
        self.ae.m_info("Analyzing %s..." % self.crash_filename)
        file_binary = self.fo.get_base64_contents(self.crash_filename)

        if file_binary:
            self.file_info = (self.crash_filename, file_binary)

        # If the event is a crash...
        self.ae.m_warn("Crash detected, analyzing...")

        name = "TODO"
        # Crashing file contents in Base64
        if self.file_info:
            binary_contents = self.file_info

        else:
            binary_contents = None

        crash_properties = dict()

        node_properties = self.utils.get_platform_info()
        if node_properties:
            crash_properties['node_id'] = node_properties['node_name']
            crash_properties['machine'] = node_properties['machine']
            crash_properties['cpu'] = node_properties['processor']

        else:
            crash_properties['node_id'] = 'Unknown'
            crash_properties['machine'] = 'Unknown'
            crash_properties['cpu'] = 'Unknown'

            crash_properties['victim'] = self.victim_filename
            crash_properties['event_name'] = name
            crash_properties['ip'] = 'Unknown'
            crash_properties['exploitability'] = 'Unknown'
            crash_properties['bin'] = binary_contents

            # Store the crash, locally and in server
            self.fo.save_crash_file(self.crash_filename, 'crashes')
            self.parent.mo.crash_data = crash_properties
