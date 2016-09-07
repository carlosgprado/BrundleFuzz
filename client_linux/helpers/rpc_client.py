############################################################
# RPC_CLIENT.PY
# Based on pika (RabbitMQ)
# Defined many queues corresponding to different kinds
# of messages and remote procedures on the server side
############################################################

import sys
import pika
import uuid


class BrundleFuzzRpcClient(object):
    def __init__(self, parent):
        """
        This module will communicate via RPC
        with RabbitMQ and ultimately with
        our fuzzing server
        """
        self.parent = parent
        self.ae = parent.ae
        self.cfg = parent.cfg
        host = self.cfg.get('server_info', 'host')

        credentials = pika.PlainCredentials(
            self.cfg.get('server_info', 'user'),
            self.cfg.get('server_info', 'pass'))

        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host = host,
                credentials = credentials,
                retry_delay = 10,
                connection_attempts = 5))

            self.ae.m_ok("Connected to server (broker): %s" % host)

        except Exception as e:
            self.ae.m_fatal("Could not connect to server")
            self.ae.m_fatal(e)

        self.channel = self.connection.channel()
        result = self.channel.queue_declare(exclusive = True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack = True,
                                   queue = self.callback_queue)

    def on_timeout(self):
        """
        This timeout kicks in when the MQ
        stops serving messages
        """
        self.ae.m_fatal("Connection timed out")
        self.ae.m_fatal("No messages received from server")
        self.ae.m_fatal("Maybe server is down?")
        self.connection.close()
        sys.exit(1)

    def on_response(self, ch, method, props, body):
        """
        Uses the correlation_id to determine
        corresponding requests and responses
        """
        if self.corr_id == props.correlation_id:
            self.response = body

    def poll_mutation_queue(self):
        """
        In this paradigm calling means pushing our message
        to the queue (the callback will take care of it)
        and wait for the response and process it.
        @returns: string, serialized MutationObject (only attributes)
        """
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange = '',   # default exchange
                                   routing_key = 'rpc_mutations_queue',
                                   properties = pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id),
                                   body = 'POLL MUTATION QUEUE')

        self.ae.m_info("[x] Sent mutation queue poll")

        while self.response is None:
            # Waiting for a response
            self.connection.process_data_events()

        return self.response

    def send_evaluation(self, mutation_object):
        """
        In this paradigm calling means pushing our message
        to the queue (the callback will take care of it)
        and wait for the response and process it.
        @returns: string, serialized MutationObject (only attributes)
        """
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange = '',   # default exchange
                                   routing_key = 'rpc_evaluations_queue',
                                   properties = pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id),
                                   # This should be a serialized
                                   # evaluation object
                                   body = mutation_object.serialize_me())

        self.ae.m_info("[x] Sent evaluation")

        while self.response is None:
            # Waiting for a response
            self.connection.process_data_events()

        return self.response
