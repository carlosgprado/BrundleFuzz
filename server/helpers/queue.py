##################################################################
# Utils.py
# Queues and stuff
##################################################################

import os
from Queue import PriorityQueue


class FuzzingQueues(object):
    def __init__(self, parent):
        self.parent = parent
        self.cfg = parent.cfg

        self.mutationQueue = PriorityQueue()
        self.processedQueueElements = list()

    def get_queue_element_by_id(self, g_id, q):
        """
        The function name is its own documentation :)
        """
        for e in q.queue:
            if e.id == g_id:
                return e

        return None

    def delete_element_with_id(self, g_id, q):
        """
        Returns a new PriorityQueue with all elements
        in q except the one with the specified g_id
        """
        p = PriorityQueue()
        for e in q.queue:
            if e.id == g_id:
                continue
            else:
                p.put(e)

        return p

    def delete_from_mutation_queue(self, g_id):
        """
        Just a thin wrapper.
        TODO: Careful with multithreading code...
        """
        p = self.delete_element_with_id(g_id, self.mutationQueue)
        self.mutationQueue = p

        return True

