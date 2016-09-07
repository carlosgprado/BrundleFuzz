##################################################################
# Bitmap.py
# The PinTool (C++) measures this during the execution on client
# side to determine code coverage
##################################################################

from array import array

UNINTERESTING = -1
CAUSED_NEW_PATH = 1
CAUSED_NEW_BIN = 2


class BitmapObject(object):
    def __init__(self, parent):
        self.parent = parent
        self.ae = parent.ae
        self.cfg = parent.cfg
        self.arr = None

    def __eq__(self, other):
        """ This equivalence takes only into
        account the code coverage, ignoring how
        many times
        """
        res = True
        for idx in xrange(self.parent.bitmap_size):
            if self.arr[idx] > 0 and other.arr[idx] > 0:
                pass
            elif self.arr[idx] == 0 and other.arr[idx] == 0:
                pass
            else:
                res = False
                break
        return res

    def compare_bitmap(self, current_bitmap):
        """
        Compares the bitmap from the last execution
        on client side with the global one.
        @returns: priority (value for the PriorityQueue)
        """
        if current_bitmap:
            priority = self._is_interesting_input(current_bitmap)

        else:
            self.ae.m_alert("Something went wrong while running under PIN. No bitmap.")
            return

        return priority

    def _is_interesting_input(self, curr_bitmap):
        """
        Compare the bitmap corresponding to the current
        trace with the history of taken paths.
        NOTE: the return values are different than the ones
        used by AFL. These values can be used as priorities
        in a PriorityQueue()
        """

        FLAG_NEW_PATH = False
        FLAG_NEW_BIN = False

        # Go through all bytes
        for idx in xrange(len(curr_bitmap)):
            curr = curr_bitmap[idx]
            hist = self.parent.history_bitmap.arr[idx]

            # Is this a completely new tuple?
            if not hist and curr:
                self.parent.history_bitmap.arr[idx] = curr
                FLAG_NEW_PATH = True

        for idx in xrange(len(curr_bitmap)):
            curr = curr_bitmap[idx]
            hist = self.parent.history_bitmap.arr[idx]

            # Hit count change? Moved to another bin?
            if curr:
                if self.parent.utils.hit_bin(curr) > self.parent.utils.hit_bin(hist):
                    self.parent.history_bitmap.arr[idx] = curr
                    FLAG_NEW_BIN = True

        if FLAG_NEW_PATH:
            return CAUSED_NEW_PATH

        elif FLAG_NEW_BIN:
            # This can be a source of noise
            # TODO: perform some tests
            # return UNINTERESTING
            return CAUSED_NEW_BIN

        else:
            return UNINTERESTING

    def get_coverage(self):
        """ Consider only not null values """
        arr = self.parent.history_bitmap.arr
        total = len(arr)
        covered = total - arr.count(0)
        coverage = ((covered + 0.0) / total) * 100

        return coverage
