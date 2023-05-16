import json
import random
from threading import Timer


class FakeNet:
    """
    Simulates a network by using events to enable simpler testing.
    """
    def __init__(self, chance_message_fails=0, message_delay=0):
        """
        Specifies a chance of a message failing to be sent and the maximum delay of a message (in milliseconds) if it is sent.

        This version is designed to simulate more realistic network conditions for testing.

        The message_delay parameter is the maximum -- a message may be delayed any amount of time between 0 ms and the delay specified.

        :param chance_message_fails: Should be in the range of 0 to 1.
        :param message_delay: Time that a message may be delayed.
        """
        self.clients = {}
        self.chance_message_fails = chance_message_fails
        self.message_delay_max = message_delay

    def register(self, *client_list):
        """
        Registers clients to the network. Clients and Miners are registered by public key.

        :param client_list: clients to be registered to this network (may be Client or Miner)
        """
        for client in client_list:
            self.clients[client.address] = client

    def broadcast(self, msg, o):
        """
        Broadcasts to all clients within self.clients the message msg and payload o.

        :param msg: the name of the event being broadcasted (e.g. "PROOF_FOUND")
        :param o: payload of the message
        """
        for client in self.clients.values():
            self.send_message(client.address, msg, o)

    def send_message(self, address, msg, o):
        """
        Sends message msg and payload o directly to Client name.

        The message may be lost or delayed, with the probability defined for this instance.

        :param address: the public key address of the client or miner to which to send the message
        :param msg: the name of the event being broadcasted (e.g. "PROOF_FOUND")
        :param o: payload of the message
        """
        if not isinstance(o, object):
            raise TypeError(f"Expecting an object, but got a {type(o)}")

        # Serializing/deserializing the object to prevent cheating in single threaded mode.
        o2 = json.loads(json.dumps(o))

        client = self.clients.get(address)

        delay = random.randint(0, self.message_delay_max)

        if random.random() > self.chance_message_fails:
            def emit_message():
                client.emit(msg, o2)
            Timer(delay, emit_message).start()

    def recognizes(self, client):
        """
        Tests whether a client is registered with the network.

        :param client: the client to test for.
        :return: True if the client is already registered.
        """
        return client.address in self.clients
