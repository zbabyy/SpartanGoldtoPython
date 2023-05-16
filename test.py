from unittest import TestCase
from hashlib import sha256
import utils
import block
import blockchain
import client
import miner
import transaction

# Generating keypair for multiple test cases, since key generation is slow.
kp = utils.generateKeypair()
addr = utils.calcAddress(kp.public)

# Adding a POW target that should be trivial to match.
EASY_POW_TARGET = 2 ** 256 - 1

# Setting blockchain configuration. (Usually this would be done during the creation of the genesis block.)
blockchain.Blockchain.makeGenesis(block.Block, transaction.Transaction)


class TestUtils(TestCase):
    def test_verify_signature(self):
        sig = utils.sign(kp.private, b"hello")
        self.assertTrue(utils.verifySignature(kp.public, b"hello", sig))
        self.assertFalse(utils.verifySignature(kp.public, b"goodbye", sig))


class TestTransaction(TestCase):
    def test_total_output(self):
        outputs = [{"amount": 20, "address": "ffff"},
                   {"amount": 40, "address": "face"}]
        t = transaction.Transaction(addr, kp.public, outputs, 1, 1)
        t.sign(kp.private)
        self.assertEqual(t.totalOutput(), 61)


class TestBlock(TestCase):
    def test_add_transaction(self):
        prev_block = block.Block("8e7912")
        prev_block.balances = {addr: 500, "ffff": 100, "face": 99}

        outputs = [{"amount": 20, "address": "ffff"}, {"amount": 40, "address": "face"}]
        t = transaction.Transaction(addr, kp.public, outputs, 1, 0)

        b = block.Block(addr, prev_block)
        self.assertFalse(b.addTransaction(t))  # should fail if a transaction is not signed

        tx = transaction.Transaction(addr, kp.public, [{"amount": 20000000000000, "address": "ffff"}], 1, 1)
        tx.sign(kp.private)
        self.assertFalse(b.addTransaction(tx))  # should fail if the 'from' account does not have enough gold.

        t.sign(kp.private)
        b.addTransaction(t)
        self.assertEqual(b.balances[addr], 500 - 61)  # Extra 1 for transaction fee.
        self.assertEqual(b.balances["ffff"], 100 + 20)
        self.assertEqual(b.balances["face"], 99 + 40)

        b2 = block.Block(addr, b)
        b2.addTransaction(t)  # should ignore any transactions that were already received in a previous block.
        self.assertFalse(b2.transactions)

    def test_rerun(self):
        prev_block = block.Block("8e7912")
        prev_block.balances = {addr: 500, "ffff": 100, "face": 99}

        outputs = [{"amount": 20, "address": "ffff"}, {"amount": 40, "address": "face"}]
        t = transaction.Transaction(addr, kp.public, outputs, 1, 0)

        b = block.Block(addr, prev_block)
        t.sign(kp.private)
        b.addTransaction(t)

        # Wiping out balances and then rerunning the block
        b.balances = {}
        b.rerun(prev_block)

        # Verifying prevBlock's balances are unchanged.
        self.assertEqual(prev_block.balances[addr], 500)
        self.assertEqual(prev_block.balances["ffff"], 100)
