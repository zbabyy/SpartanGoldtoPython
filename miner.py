from block import Block
import blockchain
from client import Client


class Miner(Client):
    def __init__(self, name=None, net=None, startingBlock: Block = None, keyPair=None,
                 miningRounds=blockchain.NUM_ROUNDS_MINING):
        super().__init__(name=name, net=net, startingBlock=startingBlock, keyPair=keyPair)
        self.miningRounds = miningRounds
        self.transactions = set()

    def initialize(self):
        self.startNewSearch()
        self.on(blockchain.START_MINING, self.findProof)
        self.on(blockchain.POST_TRANSACTION, self.addTransaction)
        self.emit(blockchain.START_MINING)

    def startNewSearch(self, txSet=None):
        self.currentBlock = blockchain.makeBlock(self.address, self.lastBlock)
        txSet = set() if txSet is None else txSet
        for tx in txSet:
            self.transactions.add(tx)
        for tx in self.transactions:
            self.currentBlock.addTransaction(tx, self)
        self.transactions.clear()
        self.currentBlock.proof = 0

    def findProof(self, oneAndDone=False):
        pausePoint = self.currentBlock.proof + self.miningRounds
        while self.currentBlock.proof < pausePoint:
            if self.currentBlock.hasValidProof():
                print(f'found proof for block {self.currentBlock.chainLength}: {self.currentBlock.proof}')
                self.announceProof()
                self.receiveBlock(self.currentBlock)
                break
            self.currentBlock.proof += 1
        if not oneAndDone:
            self.emit(blockchain.START_MINING)

    def announceProof(self):
        self.net.broadcast(blockchain.PROOF_FOUND, self.currentBlock)

    def receiveBlock(self, s):
        b = super().receiveBlock(s)
        if b is None:
            return None
        if self.currentBlock and b.chainLength >= self.currentBlock.chainLength:
            print('cutting over to new chain.')
            txSet = self.syncTransactions(b)
            self.startNewSearch(txSet)
        return b

    def syncTransactions(self, nb):
        cb = self.currentBlock
        cbTxs = set()
        nbTxs = set()
        while cb is not None and cb != nb.commonAncestor:
            for tx in cb.transactions:
                cbTxs.add(tx)
            cb = cb.previousBlock
        for tx in nb.transactions:
            nbTxs.add(tx)
        txSet = cbTxs - nbTxs
        for tx in txSet:
            self.currentBlock.addTransaction(tx, self)
        return txSet
