############################################################
# COMMON.PY
# These are data structures common to client and server
# They need to be defined in both scopes due to
# pickling / unpickling
############################################################

try:
    import cPickle as pickle

except ImportError:
    import pickle


class MutationObject(object):
    """This is a convenience object.

    Example:
    q = Queue.PriorityQueue()
    q.put(MutationObject(1, 'c:\\tests\\file.123.txt', 123, data, arr))
    """
    def __init__(self, priority = 10, filename = '', g_id = 0, p_id = 0,
        data = None, arr = None, crash_data = None):

        self.priority = priority
        self.filename = filename
        self.id = g_id
        self.p_id = p_id
        self.data = data
        self.arr = arr
        self.crash_data = crash_data

    def __cmp__(self, other):
        # This is the criteria used by the PriorityQueue
        # to... prioritize some values
        return cmp(self.priority, other.priority)

    def __repr__(self):
        """Useful for debugging"""
        s = "MutationObject\n"

        for k, v in self.__dict__.iteritems():
            s += "%s : %s\n" % (k, v)

        return s

    def serialize_me(self):
        """A serialized version of the class itself.

        It is a convenient form of sending data between machines, since
        MQ RPC allows only str or unicode to be sent as message.
        """
        return pickle.dumps(self)
