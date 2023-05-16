from threading import Timer

from blockchain import Blockchain
from block import Block
from client import Client
from miner import Miner
import transaction
from fake_net import FakeNet

print("Starting simulation. This may take a moment...")

fake_net = FakeNet()

# Clients
alice = Client(name="Alice", net=fake_net)
bob = Client(name="Bob", net=fake_net)
charlie = Client(name="Charlie", net=fake_net)

# Miners
minnie = Miner(name="Minnie", net=fake_net)
mickey = Miner(name="Mickey", net=fake_net)

# Creating genesis block
genesis: Block = Blockchain.makeGenesis(blockClass=Block.__class__,
                                        transactionClass=transaction.Transaction.__class__,
                                        clientBalanceMap={
                                            alice: 233,
                                            bob: 99,
                                            charlie: 67,
                                            minnie: 400,
                                            mickey: 300,
                                        })

# Late miner - Donald has more mining power, represented by the mining_rounds.
# (Mickey and Minnie have the default of 2000 rounds).
donald = Miner(name="Donald", net=fake_net, startingBlock=genesis, miningRounds=3000)


def show_balances(client):
    print(f"Alice has {client.lastBlock.balanceOf(alice.address)} gold.")
    print(f"Bob has {client.lastBlock.balanceOf(bob.address)} gold.")
    print(f"Charlie has {client.lastBlock.balanceOf(charlie.address)} gold.")
    print(f"Minnie has {client.lastBlock.balanceOf(minnie.address)} gold.")
    print(f"Mickey has {client.lastBlock.balanceOf(mickey.address)} gold.")
    print(f"Donald has {client.lastBlock.balanceOf(donald.address)} gold.")


# Showing the initial balances from Alice's perspective, for no particular reason.
print("Initial balances:")
show_balances(alice)

fake_net.register(alice, bob, charlie, minnie, mickey)

# Miners start mining.
minnie.initialize()
mickey.initialize()

# Alice transfers some money to Bob.
print(f"Alice is transferring 40 gold to {bob.address}")
alice.post_transaction([{"amount": 40, "address": bob.address}])


def late_miner():
    print()
    print("***Starting a late-to-the-party miner***")
    print()
    fake_net.register(donald)
    donald.initialize()


# Call the late_miner function after 2 seconds.
Timer(2, late_miner).start()


# Print out the final balances after it has been running for some time.
def print_final_balances():
    print()
    print(f"Minnie has a chain of length {minnie.current_block.chain_length}:")

    print()
    print(f"Mickey has a chain of length {mickey.current_block.chain_length}:")

    print()
    print(f"Donald has a chain of length {donald.current_block.chain_length}:")

    print()
    print("Final balances (Minnie's perspective):")
    show_balances(minnie)

    print()
    print("Final balances (Alice's perspective):")
    show_balances(alice)

    print()
    print("Final balances (Donald's perspective):")
    show_balances(donald)

    exit(0)


# Call the print_final_balances function after 5 seconds.
Timer(5, print_final_balances).start()
