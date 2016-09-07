#
# File operations.
# TODO: get parameters from the config file
# TODO: like directories, etc.
#

import glob
import os
import shutil
import random


class FileOperations(object):
    def __init__(self, parent):
        self.filename_p = 'saved_status.p'
        self.parent = parent
        self.cfg = parent.cfg

    def copy_all_files(self, source_dir, dest_dir):
        """
        It does what it says :)
        """
        self.ae.m_info("Copying all files from %s to %s" % (source_dir, dest_dir))
        for filename in glob.glob(os.path.join(source_dir, '*.*')):
            shutil.copy(filename, dest_dir)

    def save_crash_file(self, crash_file, crash_dir):
        """
        Convenience wrapper
        """
        self.ae.m_info("Saving crash file (locally): %s" % crash_file)
        shutil.move(crash_file, crash_dir)

    def save_hang_file(self, hang_file, hang_dir):
        """
        Another thin wrapper
        """
        self.ae.m_warn("Saving hang file locally (check manually!): %s" % hang_file)
        shutil.copy(hang_file, hang_dir)

    def get_random_filename(self, dir):
        """
        It returns a random filename from a directory
        """
        files = os.listdir(dir)
        if files:
            rand_idx = random.randint(0, len(files) - 1)
            return files[rand_idx]

        else:
            raise Exception('Directory is empty!')

    def get_all_filenames(self, dir):
        """
        Returns a list of absolute filename + path
        within the given directory
        """
        return glob.glob(os.path.join(dir, '*.*'))

    def gen_random_filename(self, mutations_dir, orig_name):
        """
        Generates a random filename.
        Twenty alphanumeric characters.
        """
        suffix = orig_name.split('.')[-1]
        random_string = self.parent.utils.random_alphabetical_string(20, True)
        random_filename = random_string + '.' + suffix

        return os.path.join(mutations_dir, random_filename)

    def get_base64_contents(self, file):
        """
        Get the file contents and
        encode then in Base64
        :param file: filename + path
        :return: None or Base64 string
        """
        try:
            with open(file, 'rb') as f:
                return f.read().encode('base64')

        except:
            return None
