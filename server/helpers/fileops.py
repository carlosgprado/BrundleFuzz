#
# File operations.
# TODO(carlos): get parameters from the config file
# TODO(carlos): like directories, etc.
#

from datetime import datetime
import glob
import os
import random
import shutil

try:
    import cPickle as pickle

except ImportError:
    import pickle


class FileOperations(object):
    def __init__(self, parent):
        self.parent = parent
        self.utils = parent.utils
        self.cfg = parent.cfg
        self.ae = parent.ae
        self.backup_dir = parent.backup_dir
        self.filename_p = os.path.join(self.backup_dir, 'saved_status.p')
        self.filename_q = os.path.join(self.backup_dir, 'saved_queues.p')

    def copy_all_files(self, source_dir, dest_dir):
        """It does what it says :)"""
        self.ae.m_info("Copying all files from %s to %s"
            % (source_dir, dest_dir))
        for filename in glob.glob(os.path.join(source_dir, '*.*')):
            shutil.copy(filename, dest_dir)

    def save_crash_file(self, crash_file):
        """Convenience wrapper"""
        self.ae.m_warn("Saving crash file (locally): %s" % crash_file)
        shutil.copy(crash_file, self.parent.crashes_dir)

    def get_random_filename(self, dir):
        """It returns a random filename from a directory"""
        files = os.listdir(dir)
        if files:
            rand_idx = random.randint(0, len(files) - 1)
            return files[rand_idx]

        else:
            raise Exception('Directory is empty!')

    def get_all_filenames(self, dir):
        """Exactly that.

        Returns a list of absolute filename + path
        within the given directory
        """
        return glob.glob(os.path.join(dir, '*.*'))

    def gen_random_filename(self, mutations_dir, orig_name):
        """Generates a random filename.

        Twenty alphanumeric characters.
        """
        suffix = orig_name.split('.')[-1]
        random_string = self.parent.utils.random_alphabetical_string(20, True)
        random_filename = random_string + '.' + suffix

        return os.path.join(mutations_dir, random_filename)

    def save_fuzzing_status(self, victim_filename, history_bitmap):
        """Save bitmap to file"""
        pickle_contents = dict()
        pickle_contents['name'] = victim_filename
        pickle_contents['time'] = datetime.now()
        pickle_contents['bitmap'] = history_bitmap

        if os.path.isfile(self.filename_p):
            # The file exists already
            dt = datetime.now().strftime('%d-%m-%Y-%H-%M-%S')
            backup_filename = "%s.backup_%s" % (self.filename_p, dt)
            shutil.copy(self.filename_p, backup_filename)

        with open(self.filename_p, 'w+b') as f:
            pickle.dump(pickle_contents, f)

    def save_queue_status(self, fq):
        """This is kind of fucked up.

        For every MutationObject in the mutationQueue, I will save
        its pickled string into a list. These pickled objects are not complete
        but from them I'll be able to recover their attributes later.
        """
        queue_pickled_list = []

        for mo in fq.mutationQueue.queue:
            queue_pickled_list.append(mo.serialize_me())

        # Now we have a list of strings [p_str1, p_str2]
        # Each string representing a MutationObject
        # Let's pickle this to continue this insanity :)

        if os.path.isfile(self.filename_q):
            # The file exists already
            dt = datetime.now().strftime('%d-%m-%Y-%H-%M-%S')
            backup_filename = "%s.backup_%s" % (self.filename_q, dt)
            shutil.copy(self.filename_q, backup_filename)

        with open(self.filename_q, 'w+b') as f:
            pickle.dump(queue_pickled_list, f)

    def restore_saved_status(self):
        """Restore the saved bitmap

        From a pickle dump to file
        :return: bitmap object or None
        """
        if os.path.isfile(self.filename_p):
            self.ae.m_info("Found backup bitmap file (%s)" % self.filename_p)

            with open(self.filename_p, 'rb') as fp:
                saved_status = pickle.load(fp)

            self.ae.m_ok("Restored previously saved bitmap:")
            self.ae.m_ok("    Victim: %s" % saved_status['name'])
            self.ae.m_ok("    Timestamp: %s" % str(saved_status['time']))

            return saved_status

        else:
            return None

    def restore_saved_queue(self, fq):
        """Restore the serialized queue

        :return: new FuzzingQueues object or None
        """
        if os.path.isfile(self.filename_q):
            self.ae.m_info("Found saved queue file (%s)" % self.filename_q)
            self.ae.m_info("This may take a while...")

            with open(self.filename_q, 'rb') as f:
                queue_picked_list = pickle.load(f)

            r_idx = 0

            for e in queue_picked_list:
                tmp_obj = pickle.loads(e)
                # Is there a corresponding element in the queue?
                # TODO(carlos): this is O(n^2) at the very least
                for mo in fq.mutationQueue.queue:
                    if self.strip_path(mo.filename) == tmp_obj.filename:
                        mo.priority = tmp_obj.priority
                        mo.id = tmp_obj.id
                        mo.p_id = tmp_obj.p_id
                        mo.crash_data = tmp_obj.crash_data
                        r_idx += 1

            queue_size = fq.mutationQueue.qsize()

            self.ae.m_ok("Restored previously saved queue status")
            self.ae.m_ok("\tRecovered: %r elements from %r files"
                % (r_idx, queue_size))

        else:
            self.ae.m_alert("No saved queue file found")
            self.ae.m_alert("Starting from scratch...")

        return fq

    def get_base64_contents(self, file):
        """Get the file contents in Base64

        :param file: filename + path
        :return: None or Base64 string
        """
        try:
            with open(file, 'rb') as f:
                return f.read().encode('base64')

        except Exception:
            return None

    def strip_path(self, filepath):
        """Convenience function.

        Strips path from filename.
        Ex: /a/b/filename -> filename
        """
        return filepath.split(os.sep)[-1]
