##################################################################
# Utils.py
# Server side utilities
##################################################################

import random
import string
import math


class Utils(object):
    def __init__(self, parent):
        self.parent = parent
        self.cfg = parent.cfg

    def random_url(self, max_url_len = 1024):
        """ Returns a random URL """
        prefix = 'http://'
        suffix = '.com/announce'

        rand_url = prefix + self.random_string(max_url_len) + suffix

        return rand_url

    def random_alphabetical_string(self, maxlen = 1024, exact = False):
        """
        Filenames are usually rejected if they contain
        funky characters, blocking execution
        """
        if exact:
            string_len = maxlen

        else:
            string_len = random.randint(1, maxlen)

        alphabet = string.ascii_letters + string.digits

        s = ''.join(random.choice(alphabet) for _ in range(string_len))

        return s

    def random_string(self, maxlen = 1024):
        """
        Returns a random string, UTF-8 encoded
        """
        string_len = random.randint(1, maxlen)
        alphabet = string.ascii_letters + string.digits + string.punctuation

        s = ''.join(random.choice(alphabet) for _ in range(string_len))

        return s

    def random_byte_string(self, maxlen = 1024):
        """
        Returns a string of random bytes (excluding zero)
        """
        s = ''.join(chr(random.randint(1, 255)) for _ in range(maxlen))

        return s

    def random_int(self, min_int = 1, max_int = 10240):
        """
        Convenience function. Returns an integer
        """
        return random.randint(min_int, max_int)

    def random_hexstring(self, string_len = 10240):
        """
        Returns a random hex string
        """
        alphabet = string.digits + 'abcdef'
        hex_string = ''.join(random.choice(alphabet) for _ in range(string_len))

        return hex_string

    def H(self, data):
        """
        Implementation of Shannon's Entropy
        Ero Carrera is the man
        """
        entropy = 0

        if not data:
            return entropy

        for x in range(256):
            p_x = float(data.count(chr(x))) / len(data)
            if p_x > 0:
                entropy -= p_x * math.log(p_x, 2)

        return entropy

    def entropy_scan(self, data, block_size):
        """
        Implemented as a generator.
        Did I mention Ero is the man?
        """
        for block in (
            data[x: block_size + x]
            for x in range(len(data) - block_size)):

            yield self.H(block)

    def get_size_uint32(self):
        """
        Let's do things right.
        Calculate the size of an unsigned long
        for this architecture. Or 4 :)
        """
        try:
            import ctypes
            return ctypes.sizeof(ctypes.c_uint32)

        except:
            print "[!] WARNING: Could not find ctypes. Assuming uint32 is 4 bytes :("
            return 4

    def hit_bin(self, n):
        """
        Given a hit number, return the corresponding bin
        Hit bins: {1, 2, 3, 4-7, 8-15, 16-31, 32-127, 128+}
        """
        # TODO: fix this monkey code!

        if n < 4:
            return n
        elif n << 3 == 0:
            return 4
        elif n << 4 == 0:
            return 5
        elif n << 5 == 0:
            return 6
        elif n >= 32 and n <= 127:
            return 7
        else:
            return 8
