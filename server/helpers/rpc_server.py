##########################################
# RPC_SERVER.PY
# Based on pika (RabbitMQ)
##########################################

import pika

try:
    import cPickle as pickle
except ImportError:
    import pickle


UNINTERESTING = -1
CAUSED_NEW_PATH = 1
CAUSED_NEW_BIN = 2
CAUSED_CRASH = 3


class BrundleFuzzRpcServer(object):
    def __init__(self, parent):
        self.parent = parent
        self.cfg = parent.cfg
        self.ae = parent.ae
        self.fq = parent.fuzzing_queues
        self.utils = parent.utils
        self.fo = parent.fileops
        self.cth = parent.cthulhu

        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host = 'localhost'))
            self.ae.m_ok("Successfully connected to message queue (broker)")

        except Exception:
            self.ae.m_fatal("[!] Could not connect to the message queue!")

        self.channel = self.connection.channel()

        ###########################################################
        # Declare queue serving mutations to clients
        ###########################################################
        self.channel.queue_declare(queue = 'rpc_mutations_queue')
        self.channel.basic_qos(prefetch_count = 1)
        self.channel.basic_consume(self.on_mutation_request,
            queue = 'rpc_mutations_queue')

        ###########################################################
        # Declare queue receiveing mutation objects from clients
        ###########################################################
        self.channel.queue_declare(queue = 'rpc_evaluations_queue')
        self.channel.basic_qos(prefetch_count = 1)
        self.channel.basic_consume(self.on_evaluation_request,
            queue = 'rpc_evaluations_queue')

    def on_mutation_request(self, ch, method, props, body):
        """Callback for messages in the 'rpc_mutations_queue'

        They say: "Hey, do you have a mutation for me?"
        """

        # This is the "remote procedure"
        # being called and returning a value
        mutation_obj = self.get_mutation()

        ch.basic_publish(exchange = '',
                         routing_key = props.reply_to,
                         properties = pika.BasicProperties(
                                    correlation_id = props.correlation_id),
                         body = mutation_obj.serialize_me())

        ch.basic_ack(delivery_tag = method.delivery_tag)

    def on_evaluation_request(self, ch, method, props, body):
        """Callback for messages in the 'rpc_evaluations_queue'

        They say: "Hey, here are the execution results"
        """

        # This is the "remote procedure"
        # being called and returning a value
        ev_mutation_object = pickle.loads(body)
        self.process_execution_results(ev_mutation_object)

        ch.basic_publish(exchange = '',
                         routing_key = props.reply_to,
                         properties = pika.BasicProperties(
                                    correlation_id = props.correlation_id),
                         body = 'EVALUATION RECEIVED')

        ch.basic_ack(delivery_tag = method.delivery_tag)

    def get_mutation(self):
        """Simply gets a mutation object

        Takes element from the Priority Queue
        :return: MutationObject object
        """
        PERIODICITY = 10
        if self.parent.g_id > 0:
            if self.parent.g_id % PERIODICITY == 0:
                self.parent.maintenance_tasks()

        mo = self.cth.generate_test_case()

        return mo

    def process_execution_results(self, emo):
        """Receives and processes an evaluation

        The evaluation is a mutation object from a client.
        It checks:
            * bitmap corresponding execution
            * crash dictionary (if any)
        """
        if emo.priority == CAUSED_CRASH:
            # SET ON CLIENT SIDE
            # Insert into the SQLite DB
            crash_properties = emo.crash_data
            self.parent.crash_db.write_crash(crash_properties)
            self.cth.test_case_to_file(emo.data, emo.filename)
            self.fo.save_crash_file(emo.filename)
            # Remove unnecessary overhead for the queue
            emo.data = None
            self.fq.mutationQueue.put(emo)
            return

        # This did not cause a crash on client side
        emo.priority = self.parent.history_bitmap.compare_bitmap(emo.arr)

        if emo.priority == UNINTERESTING:
            # This execution did not cause
            # anything interesting to happen
            return

        else:
            # Write the test case to mutations dir
            self.cth.test_case_to_file(emo.data, emo.filename)
            # Remove unnecessary overhead for the queue
            emo.data = None
            self.fq.mutationQueue.put(emo)

    def run(self):
        """This is a convenience wrapper"""
        self.channel.start_consuming()
