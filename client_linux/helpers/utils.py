##################################################################
# Utils.py
# Client side utilities
##################################################################

import platform


class Utils(object):
    def __init__(self, parent):
        self.parent = parent
        self.ae = parent.ae
        self.cfg = parent.cfg

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
            self.ae.m_warn("WARNING: Could not find ctypes. Assuming uint32 is 4 bytes :(")
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

    def get_platform_info(self):
        """
        Information regarding the computer
        where the fuzzer is running
        """
        try:
            node_properties = {
                'node_name' : platform.node(),
                'os_release': platform.release(),
                'os_version': platform.version(),
                'machine'   : platform.machine(),
                'processor' : platform.processor()
            }
        except:
            self.ae.m_alert('[x] Error getting platform information')
            return None

        return node_properties
