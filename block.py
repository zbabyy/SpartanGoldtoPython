import json

import utils
import time
import transaction

POW_BASE_TARGET = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
COINBASE_AMT_ALLOWED = 25

class Block:
    def __init__(self, rewardAddr = None, prevBlock=None, target=POW_BASE_TARGET,
                 coinbaseReward=COINBASE_AMT_ALLOWED):
        self.prevBlockHash = prevBlock.hashVal() if prevBlock else None
        self.target = target

        # Get the balances and nonces from the previous block, if available.
        # Note that balances and nonces are NOT part of the serialized format.
        self.balances = prevBlock.balances.copy() if prevBlock else {}
        self.nextNonce = prevBlock.nextNonce.copy() if prevBlock else {}

        if prevBlock and prevBlock.rewardAddr:
            # Add the previous block's rewards to the miner who found the proof.
            winnerBalance = self.balanceOf(prevBlock.rewardAddr) or 0
            self.balances[prevBlock.rewardAddr] = winnerBalance + prevBlock.totalRewards()

        # Storing transactions in an OrderedDict to preserve key order.
        self.transactions = {}

        # Used to determine the winner between competing chains.
        # Note that this is a little simplistic -- an attacker
        # could make a long, but low-work chain.  However, this works
        # well enough for us.
        self.chainLength = prevBlock.chainLength + 1 if prevBlock else 0

        self.timestamp = int(time.time() * 1000)

        # The address that will gain both the coinbase reward and transaction fees,
        # assuming that the block is accepted by the network.
        self.rewardAddr = rewardAddr

        self.coinbaseReward = coinbaseReward

    def isGenesisBlock(self):
        return self.chainLength == 0

    def hasValidProof(self):
        h = utils.hashe(self.serialize())
        n = int(h, 16)
        return n < self.target

    def serialize(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def toJSON(self):
        return {
            'chainLength': self.chainLength,
            'prevBlockHash': self.prevBlockHash,
            'target': self.target,
            'balances': self.balances,
            'nextNonce': self.nextNonce,
            'transactions': self.transactions,
            'chainLength': self.chainLength,
            'timestamp': self.timestamp,
            'rewardAddr': self.rewardAddr,
            'coinbaseReward': self.coinbaseReward,
        }

    def hashVal(self):
        return utils.hashe(self.serialize())

    @property
    def id(self):
        return self.hashVal()

    def addTransaction(self, tx: transaction.Transaction, client=None) -> bool:
        if tx.id in self.transactions:
            if client:
                client.log(f"Duplicate transaction {tx.id}.")
            return False
        elif tx.sig is None:
            if client:
                client.log(f"Unsigned transaction {tx.id}.")
            return False
        elif not tx.validSignature():
            if client:
                client.log(f"Invalid signature for transaction {tx.id}.")
            return False
        elif not tx.sufficientFunds(self):
            if client:
                client.log(f"Insufficient gold for transaction {tx.id}.")
            return False

        nonce = self.nextNonce.get(tx.from_, 0)
        if tx.nonce < nonce:
            if client:
                client.log(f"Replayed transaction {tx.id}.")
            return False
        elif tx.nonce > nonce:
            if client:
                client.log(f"Out of order transaction {tx.id}.")
            return False
        else:
            self.nextNonce[tx.from_] = nonce + 1

        self.transactions[tx.id] = tx

        sender_balance = self.balanceOf(tx.from_)
        self.balances[tx.from_] = sender_balance - tx.totalOutput()

        for output in tx.outputs:
            amount, address = output
            old_balance = self.balanceOf(address)
            self.balances[address] = amount + old_balance

        return True

    def rerun(self, prevBlock) -> bool:
        self.balances = prevBlock.balances.copy()
        self.nextNonce = prevBlock.nextNonce.copy()

        if self.rewardAddr:
            winner_balance = self.balanceOf(prevBlock.rewardAddr)
            self.balances[self.rewardAddr] = winner_balance + self.totalRewards()

        txs = list(self.transactions.values())
        self.transactions = {}
        for tx in txs:
            success = self.addTransaction(tx)
            if not success:
                return False

        return True

    def balanceOf(self, addr: str) -> float:
        return self.balances.get(addr, 0.0)

    def totalRewards(self) -> float:
        return sum(tx.fee for tx in self.transactions.values()) + self.coinbaseReward

    def contains(self, tx: transaction.Transaction) -> bool:
        return tx.id in self.transactions

