##################################################################
# BrundleFuzzClient.py
# The core (Python) reads the feedback information from
# the PinTool (C++) from the shared memory
##################################################################


import sys
import os
import mmap
import subprocess
from array import array
import logging
import logging.handlers
from datetime import datetime
from ConfigParser import SafeConfigParser

try:
    import cPickle as pickle
except:
    import pickle

# This is necessary because a MutationObject will
# be unserialized from the server.
# It needs to exist in this namespace
from helpers.common import MutationObject

from helpers.utils import Utils
from helpers.crash_analysis import CrashAnalysis
from helpers.rpc_client import BrundleFuzzRpcClient
from helpers.fileops import FileOperations
from helpers.aesthetics import Aesthetics

# Some nice named constants
CAUSED_CRASH = 3


class BrundleFuzzClient(object):
    def __init__(self):

        self.debug = False
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.mutations_dir = os.path.join(self.root_dir, 'mutations')
        self.hangs_dir = os.path.join(self.root_dir, 'hangs')
        self.cfg = self._initialize_config()
        self.ml = self._initialize_logging()
        self.mo = None

        # Shared memory
        self.shm = None
        self.shm_size = 0
        self.bitmap_size = 65536
        self.fd = 0
        # PIN command line
        self.cmd_l = []

        # Setup helpers
        self.ae = Aesthetics(self)
        self.utils = Utils(self)
        self.fileops = FileOperations(self)
        self.crash_analysis = CrashAnalysis(self)
        self.rpc_client = BrundleFuzzRpcClient(self)

        self._initialize_shared_memory()
        self._initialize_pin_cmd()

    def _initialize_config(self):
        """
        This config will be shared with helper
        modules via the parent attribute
        """
        cfg = SafeConfigParser()
        cfg.read('config.ini')

        return cfg

    def _initialize_logging(self):
        """
        Printing to console is dirty
        """
        main_logger = logging.getLogger('main')

        log_filename = os.path.join('logs', 'log.txt')
        main_logger.setLevel(logging.DEBUG)

        # 5 rotating logs of 1 MB each
        handler = logging.handlers.RotatingFileHandler(
            log_filename,
            maxBytes = 1024 * 1024,
            backupCount = 1
        )

        main_logger.addHandler(handler)

        return main_logger

    def _initialize_shared_memory(self):
        """
        This is the IPC channel between us (Python)
        and the PinTool (C/C++)
        """
        s_uint32 = self.utils.get_size_uint32()
        shm_name = "/tmp/NaFlSharedMemory"

        self.shm_size = self.bitmap_size * s_uint32  # architecture dependent :)

        self.fd = open(shm_name, 'a+b')
        # "Stretch" the file to be mapped
        self.fd.write("\x00" * self.shm_size)

    def _initialize_pin_cmd(self):
        """
        Initializes fuzzing parameters with
        information stored in a config file
        """
        self.cmd_l.append(self.cfg.get('pin_info', 'pin_bat'))
        self.cmd_l.append('-t')
        self.cmd_l.append(self.cfg.get('pin_info', 'pintool'))
        self.cmd_l.append('-timer')
        self.cmd_l.append(self.cfg.get('pin_info', 'timeout'))
        self.cmd_l.append('-module')
        self.cmd_l.append(self.cfg.get('target_info', 'module').lower())
        self.cmd_l.append('--')
        self.cmd_l.append(self.cfg.get('target_info', 'filename'))

        # Parse the cmd options
        try:
            _options = self.cfg.get('target_info', 'cmd_options')
            for _cmd in _options.split():
                self.cmd_l.append(_cmd)
        except:
            self.ml.info('[.] No command line options found.')

        self.debug = self.cfg.getboolean('runtime', 'debug')

    def _run_under_pin(self, input_filename):
        """
        Runs the given file under PIN and
        gets the bitmap representing execution
        @returns: current execution bitmap
        """
        self.cmd_l.append(input_filename)
        subprocess.call(self.cmd_l, shell = False)
        self.cmd_l.pop()  # remove the filename from cmd :)

        # The PinTool has written its feedback into
        # the shared memory. Time to read it.
        self.fd.seek(0)  # file-like interface

        # This coerces somehow the bitmap to an array of ulong's
        curr_bitmap = array('L', self.fd.read(self.shm_size))  # C ulong (4 bytes)

        return curr_bitmap

    def _fuzzing_loop(self):
        """
        Fuzzing Loop.
        This loops (maybe indefinitely) creating several
        fuzzing processes
        """
        iteration_nr = 0

        while True:
            # subprocess.call() is blocking, exactly what I need :)
            # Execution continues when this subprocess returns, either:
            # * instrumented process exits
            # * instrumented process crashes
            # * timeout expires (implemented in PinTool)

            if iteration_nr % 10 == 0:
                self.ae.m_info("* Iteration #%d" % iteration_nr)
                self.ae.m_info("* PLACEHOLDER. PERIODIC MAINTENANCE PROCESSES")

                iteration_nr += 1
                continue

            # Mutation objects are read from the queue
            smo = self.rpc_client.poll_mutation_queue()
            self.mo = pickle.loads(smo)

            if self.mo:
                input_filename = self.mo.filename

                data = self.mo.data
                input_path_filename = os.path.join(self.mutations_dir, input_filename)
                with open(input_path_filename, 'wb') as f:
                    f.write(data)

                # Run with the newly created file unde PIN
                curr_bitmap = self._run_under_pin(input_path_filename)

            else:
                self.ae.m_alert("Problem getting MutationObject from server")
                self.ae.m_alert("Continuing...")
                continue

            #####################################################
            # Check if this was a crash on client side
            # This way I can analyze it inmediately
            #####################################################
            if curr_bitmap[0] == 0x41414141 \
                and curr_bitmap[1] == 0x42424242:
                # Restore these first bytes to more appropriate values
                curr_bitmap[0] = 0
                curr_bitmap[1] = 0

                self.ml.info('**** CRASH ****' * 4)
                self.ml.info(input_filename)

                self.mo.priority == CAUSED_CRASH

                # Analyzes the crash (and saves it, if determined interesting)
                # This sets the MutationObject crash_data attribute
                cmd = [self.cfg.get('target_info', 'filename'), input_filename]
                self.crash_analysis.analyze_crash(cmd)

            # The bitmap regarding the current execution
            self.mo.arr = curr_bitmap

            # Delete the temporary file from disk
            if os.path.exists(input_path_filename):
                os.remove(input_path_filename)

            # Information is sent back to the server
            self.rpc_client.send_evaluation(self.mo)

            iteration_nr += 1

    def run(self):
        """
        This prepares the run and starts the fuzzing loop
        """

        victim_filename = self.cfg.get('target_info', 'filename')
        self.ml.info("")
        self.ml.info("=" * 80)
        self.ml.info("Fuzzing initiated from the command line.")
        self.ml.info("Started fuzzing: %s" % victim_filename)
        self.ml.info("Timestamp: %s" % str(datetime.now()))

        try:
            self._fuzzing_loop()  # never returns

        except KeyboardInterrupt:
            self.ae.m_alert("""
                ============================================
                ===                                      ===
                === Fuzzing cancelled by user (Ctrl + C) ===
                === Exiting...                           ===
                ===                                      ===
                ============================================
                """)

            self.fd.close()
            self.rpc_client.connection.close()
            sys.exit(1)


def main():
    """
    This must be kept to the bare minimum
    """
    bf = BrundleFuzzClient()
    bf.run()


if __name__ == '__main__':
    main()
