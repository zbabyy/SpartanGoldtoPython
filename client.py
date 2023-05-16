from events import Events

import blockchain
from block import Block
import utils

class Client(Events):
    lastConfirmedBlock: Block
    lastBlock: Block

    def __init__(self, name=None, net=None, startingBlock=None, keyPair=None):
        super().__init__()
        self.net = net
        self.name = name

        if keyPair is None:
            self.keyPair = utils.generateKeypair()
        else:
            self.keyPair = keyPair

        self.address = utils.calcAddress(self.keyPair['public'])

        self.nonce = 0
        self.pendingOutgoingTransactions = {}
        self.pendingReceivedTransactions = {}
        self.blocks = {}
        self.pendingBlocks = {}

        if startingBlock:
            self.setGenesisBlock(startingBlock)

        self.on(blockchain.PROOF_FOUND, self.receiveBlock)
        self.on(blockchain.MISSING_BLOCK, self.provideMissingBlock)

    def setGenesisBlock(self, startingBlock):
        if self.lastBlock:
            raise Exception("Cannot set genesis block for existing blockchain.")
        self.lastConfirmedBlock = Block(startingBlock)
        self.lastBlock = Block(startingBlock)
        self.blocks[startingBlock.id] = startingBlock

    @property
    def confirmedBalance(self):
        return self.lastConfirmedBlock.balanceOf(self.address)

    @property
    def availableGold(self):
        pendingSpent = sum(tx.totalOutput() for tx in self.pendingOutgoingTransactions.values())
        return self.confirmedBalance - pendingSpent

    def postTransaction(self, outputs, fee=blockchain.DEFAULT_TX_FEE):
        totalPayments = sum(output['amount'] for output in outputs) + fee
        if totalPayments > self.availableGold:
            raise Exception(f"Requested {totalPayments}, but account only has {self.availableGold}.")
        return self.postGenericTransaction(outputs=outputs, fee=fee)

    def postGenericTransaction(self, txData):
        tx = blockchain.createTransaction(txData, self.keyPair)
        self.pendingOutgoingTransactions[tx.id] = tx
        self.emit('transaction', tx)
        self.net.broadcast(tx.toJSON())
        return tx

    def receiveBlock(self, block):
        if block.prev != self.lastBlock.id:
            self.emit(blockchain.MISSING_BLOCK, block.prev)
            self.pendingBlocks.setdefault(block.prev, []).append(block)
            return

        # Confirm any transactions in this block.
        self.lastConfirmedBlock = block
        for tx in block.transactions:
            if tx.id in self.pendingReceivedTransactions:
                self.pendingReceivedTransactions.pop(tx.id)
            if tx.inputs[0]['address'] == self.address:
                self.nonce += 1
        self.lastBlock = block
        self.blocks[block.id] = block

        # Remove any pending blocks that depended on this one.
        for pendingBlock in self.pendingBlocks.pop(block.id, []):
            self.receiveBlock(pendingBlock)

    def provideMissingBlock(self, blockId):
        if blockId not in self.blocks:
            return
        self.net.sendMessage('block', self.blocks[blockId].toJSON())
