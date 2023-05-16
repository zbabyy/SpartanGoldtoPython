from typing import Dict, List, Optional, Tuple
from hashlib import sha256
import time

from block import Block

# Network message constants
MISSING_BLOCK = "MISSING_BLOCK"
POST_TRANSACTION = "POST_TRANSACTION"
PROOF_FOUND = "PROOF_FOUND"
START_MINING = "START_MINING"

# Constants for mining
NUM_ROUNDS_MINING = 2000

# Constants related to proof-of-work target
POW_BASE_TARGET = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
POW_LEADING_ZEROES = 15

# Constants for mining rewards and default transaction fees
COINBASE_AMT_ALLOWED = 25
DEFAULT_TX_FEE = 1

# If a block is 6 blocks older than the current block, it is considered
# confirmed, for no better reason than that is what Bitcoin does.
# Note that the genesis block is always considered to be confirmed.
CONFIRMED_DEPTH = 6

class Blockchain:
    cfg = {}

    @staticmethod
    def makeGenesis(blockClass: object, transactionClass: object, powLeadingZeroes: object = POW_LEADING_ZEROES,
                    coinbaseAmount: object = COINBASE_AMT_ALLOWED, defaultTxFee: object = DEFAULT_TX_FEE,
                    confirmedDepth: object = CONFIRMED_DEPTH,
                    clientBalanceMap: object = None, startingBalances: object = None) -> Block:

        if clientBalanceMap is not None and startingBalances is not None:
            raise ValueError("You may set clientBalanceMap OR set startingBalances, but not both.")

            # Setting blockchain configuration
            new = {'blockClass': blockClass, 'transactionClass': transactionClass,
                   'coinbaseAmount': coinbaseAmount, 'defaultTxFee': defaultTxFee,
                   'confirmedDepth': confirmedDepth, 'powTarget': POW_BASE_TARGET >> powLeadingZeroes}

            cfg.update(new)

        # If startingBalances was specified, we initialize our balances to that object.
        balances = startingBalances or {}

        # If clientBalanceMap was initialized instead, we copy over those values.
        if clientBalanceMap is not None:
            for client, balance in clientBalanceMap.items():
                balances[client.address] = balance

        g = Blockchain.makeBlock()

        # Initializing starting balances in the genesis block.
        for addr in balances:
            g.balances[addr] = balances[addr]

        # If client_balance_map was specified, we set the genesis block for every client.
        if clientBalanceMap:
            for client in clientBalanceMap.keys():
                client.set_genesis_block(g)

        return g

    @staticmethod
    def deserialize_block(o: Dict):
        if isinstance(o, Blockchain.cfg):
            return o

        b = Blockchain.cfg["blockClass"]()
        b.chain_length = int(o["chainLength"])
        b.timestamp = o["timestamp"]

        if b.is_genesis_block():
            # Balances need to be recreated and restored in a map.
            for client_id, amount in o["balances"]:
                b.balances[client_id] = amount
        else:
            b.prev_block_hash = o["prevBlockHash"]
            b.transactions = [
                Blockchain.cfg["transactionClass"].deserialize(t) for t in o["transactions"]
            ]
            b.nonce = o["nonce"]
            b.difficulty = o["difficulty"]
            b.hashe = o["hash"]
            b.num_txns = o["numTxns"]

        return b

    @staticmethod
    def makeBlock(*args: object) -> Block:
       # print(Blockchain.cfg.get('blockClass'))
        return Block(*args)

    @staticmethod
    def makeTransaction(o):
        if isinstance(o, Blockchain.cfg.transactionClass):
            return o
        else:
            return Blockchain.cfg.transactionClass(o)
