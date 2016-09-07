##################################################################
# BrundleFuzzServer.py
# This implements all mutation intelligence
##################################################################

from array import array
from ConfigParser import SafeConfigParser
from datetime import datetime
from Queue import PriorityQueue
import logging
import logging.handlers
import multiprocessing
import os

# This is necessary because a MutationObject will
# be unserialized from the server.
# It needs to exist in this namespace
from helpers.common import MutationObject

from helpers.aesthetics import Aesthetics
from helpers.bitmap import BitmapObject
from helpers.cthulhu import Cthulhu
from helpers.database import CrashDataBase
from helpers.fileops import FileOperations
from helpers.mutations.plugins import Plugins
from helpers.queue import FuzzingQueues
from helpers.rpc_server import BrundleFuzzRpcServer
from helpers.utils import Utils


class BrundleFuzzServer(multiprocessing.Process):
    def __init__(self):
        super(BrundleFuzzServer, self).__init__()

        self.debug = False
        self.name = 'server'
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.ae = Aesthetics(self)
        self.cfg = self._initialize_config()
        self.ml = self._initialize_logging()

        self.banner()

        # Fuzzing related
        self.victim_filename = self.cfg.get('target_info', 'filename')
        self.bitmap_size = 65536
        self.history_bitmap = BitmapObject(self)

        crashd = os.path.join(self.root_dir, 'crashes')
        if not os.path.isdir(crashd):
            os.mkdir(crashd)
        self.crashes_dir = crashd

        backupd = os.path.join(self.root_dir, 'backup')
        if not os.path.isdir(backupd):
            os.mkdir(backupd)
        self.backup_dir = backupd

        # TODO(carlos): maybe better design to move this
        # into Cthulhu a level higher?
        self.plugins = Plugins(self)
        self.g_id = 0

        # Setup helpers
        self.utils = Utils(self)
        self.fileops = FileOperations(self)
        self.crash_db = CrashDataBase(self)
        self.fuzzing_queues = FuzzingQueues(self)

        # Instantiate Cthulhu
        mutation_mode = self.cfg.get('mutations', 'mode')
        self.cthulhu = Cthulhu(self, mode = mutation_mode)

        self.rpc_server = BrundleFuzzRpcServer(self)

    def _initialize_config(self):
        """Main Config object

        This config will be shared with helper
        modules via the parent attribute
        """
        cfg = SafeConfigParser()
        cfg.read('config.ini')

        return cfg

    def _initialize_logging(self):
        """Printing to console is dirty"""
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

    def maintenance_tasks(self):
        """Regularly executed tasks

        This will be called from the rpc_server
        when the mutation g_id reaches a multiple
        of a certain number
        """
        cov = self.history_bitmap.get_coverage()

        self.ae.m_info("* MAINTENANCE TASKS ")

        self.ae.m_info("* CURRENT MUTATION ID: %d" % self.g_id)
        self.ae.m_info("* CURRENT CODE COVERAGE: %.2f %%" % cov)
        self.ae.m_info("----------------------------------")

        self._minimize_queues()

    def _minimize_queues(self):
        """ Calculate *a* minimal set of files (on the queue) which
            together cover the current bitmap
            The idea is to start calculating the union of individual
            bitmaps (from MutationObjects in self.fuzzing_queues) and
            stop when it equals self.history_bitmap """

        interim_bitmap = BitmapObject(self)
        interim_bitmap.arr = array('L', [0] * self.bitmap_size)
        interesting_queue_elements = []
        original_queue_len = len(self.fuzzing_queues.mutationQueue.queue)

        for mo in self.fuzzing_queues.mutationQueue.queue:
            tmp_bitmap = BitmapObject(self)
            tmp_bitmap.arr = mo.arr
            new_elements = 0
            for idx in xrange(self.bitmap_size):
                if tmp_bitmap.arr[idx] and not interim_bitmap.arr[idx]:
                    # This is something new!
                    interim_bitmap.arr[idx] = tmp_bitmap.arr[idx]
                    new_elements += 1

            if new_elements:
                interesting_queue_elements.append(mo)

            # NOTE: This equivalence has been
            # defined by overriding __eq__ in the class
            if interim_bitmap == self.history_bitmap:
                # Don't need to keep searching for a set
                break

        # Finished processing queue elements
        self.ae.m_info("Finished consolidating queues (%d -> %d elements)" \
                       % (original_queue_len, len(interesting_queue_elements)))

        # Remove uninteresting elemements on disk
        for mo in self.fuzzing_queues.mutationQueue.queue:
            if mo not in interesting_queue_elements:
                os.remove(mo.filename)

        # Modify the queue
        self.fuzzing_queues.mutationQueue = PriorityQueue()
        for mo in interesting_queue_elements:
            self.fuzzing_queues.mutationQueue.put(mo)

    def _fuzzing_loop(self):
        """Main fuzzing loop

        Loops indefinitely pushing mutations to one
        queue and polling evaluations from another.
        NOTE: rpc_server.run() blocks, everything
        after it will NOT be executed
        """
        self.ae.m_warn("[ STARTED FUZZING LOOP ]")

        self.rpc_server.run()

    def run(self):
        """This prepares the run and starts the fuzzing loop"""

        saved_status = self.fileops.restore_saved_status()
        if saved_status:
            self.history_bitmap.arr = saved_status['bitmap']

        if not self.history_bitmap.arr:
            self.ae.m_alert("Failed to restore saved bitmap.")
            self.ae.m_alert("Starting from scratch...")
            self.history_bitmap.arr = array('L', [0] * self.bitmap_size)

        # TODO(carlos): this API is kind of asymmetric.
        # Modify restore_saved_status maybe
        self.fileops.restore_saved_queue(self.fuzzing_queues)

        self.ae.m_ok("Server initiated from the command line.")
        self.ae.m_ok("Timestamp: %s" % str(datetime.now()))

        try:
            self._fuzzing_loop()  # never returns

        except KeyboardInterrupt:
            self.ae.m_alert("============================================")
            self.ae.m_alert("===                                      ===")
            self.ae.m_alert("=== Fuzzing cancelled by user (Ctrl + C) ===")
            self.ae.m_alert("=== Exiting...                           ===")
            self.ae.m_alert("===                                      ===")
            self.ae.m_alert("============================================")

            self.cleanup()
            return

    def cleanup(self):
        """Save the bitmap to a pickle file"""
        self.ae.m_info("Saving the fuzzing status to file...")
        self.fileops.save_fuzzing_status(self.victim_filename,
            self.history_bitmap.arr)

        self.ae.m_info("Saving the queue status to file...")
        self.fileops.save_queue_status(self.fuzzing_queues)

        self.ae.stop()

    def banner(self):
        self.ae.m_warn("""
            ____                       ____     ______
           / __ )_______  ______  ____/ / /__  / ____/_  __________
          / __  / ___/ / / / __ \/ __  / / _ \/ /_  / / / /_  /_  /
         / /_/ / /  / /_/ / / / / /_/ / /  __/ __/ / /_/ / / /_/ /_
        /_____/_/   \__,_/_/ /_/\__,_/_/\___/_/    \__,_/ /___/___/
        \tBrundle Lab. 2016.
        """)


def main():
    """Starts several processes

    This must be kept to the bare minimum
    """
    multiprocessing.log_to_stderr()
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.INFO)

    jobs = []

    try:
        bfs = BrundleFuzzServer()
        jobs.append(bfs)
        bfs.start()

        for j in jobs:
            j.join()

    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
