from utils import hashe, sign, addressMatchesKey, verifySignature

# String constants mixed in before hashing.
TX_CONST = "TX"


class Transaction:
    """
    A transaction comes from a single account, specified by "from_address". For
    each account, transactions have an order established by the nonce. A
    transaction should not be accepted if the nonce has already been used.
    (Nonces are in increasing order, so it is easy to determine when a nonce
    has been used.)
    """

    def __init__(self, from_address, nonce, pub_key, sig=None, outputs=None, fee=0, data={}):
        self.from_address = from_address
        self.nonce = nonce
        self.pub_key = pub_key
        self.sig = sig
        self.fee = fee
        self.outputs = []
        if outputs:
            for output in outputs:
                amount = int(output['amount']) if not isinstance(output['amount'], int) else output['amount']
                self.outputs.append({'amount': amount, 'address': output['address']})
        self.data = data

    @property
    def id(self):
        """
        A transaction's ID is derived from its contents.
        """
        return hashe(TX_CONST + str({
            'from': self.from_address,
            'nonce': self.nonce,
            'pubKey': self.pub_key,
            'outputs': self.outputs,
            'fee': self.fee,
            'data': self.data
        }))

    def sign(self, priv_key):
        """
        Signs a transaction and stores the signature in the transaction.

        :param priv_key: The key used to sign the signature. It should match the public key included in the transaction.
        """
        self.sig = sign(priv_key, self.id)

    def valid_signature(self):
        """
        Determines whether the signature of the transaction is valid
        and if the from address matches the public key.

        :return: Validity of the signature and from address.
        """
        return self.sig is not None and addressMatchesKey(self.from_address, self.pub_key) and verifySignature(
            self.pub_key, self.id, self.sig)

    def sufficient_funds(self, block):
        """
        Verifies that there is currently sufficient gold for the transaction.

        :param block: Block used to check current balances
        :return: True if there are sufficient funds for the transaction, according to the balances from the specified block.
        """
        return self.total_output() <= block.balances.get(self.from_address)

    def total_output(self):
        """
        Calculates the total value of all outputs, including the transaction fee.

        :return: Total amount of gold given out with this transaction.
        """
        return sum([output['amount'] for output in self.outputs]) + self.fee
