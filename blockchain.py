from configs import MAX_TRANSACTIONS_PER_BLOCK
import datetime
import hashlib
import json
from json.decoder import JSONDecodeError
from utils import standardize_key, verify_signature
import requests
from typing import List, Set
from models import Block, Transaction
import logging
from Crypto.PublicKey import RSA

logging.basicConfig(level=logging.INFO)


class Blockchain:
    def __init__(self):
        self.transactions: List[Transaction] = []

        with open("ledger.txt", "r") as f:
            chain_json = f"[{f.read()[:-1]}]"
            try:
                self.chain: List[Block] = json.loads(chain_json)
                if len(self.chain) == 0:
                    self.create_block(0, "null")
            except JSONDecodeError:
                logging.error("Cannot decode data in 'ledger.txt'.")

        with open("nodes.txt", "r") as f:
            self.nodes: Set[str] = set(
                map(lambda line: line[:-1], f.readlines())
            )

    def create_block(self, proof, previous_hash):
        block: Block = {
            "index": len(self.chain) + 1,
            "timestamp": str(datetime.datetime.now()),
            "proof": proof,
            "previous_hash": previous_hash,
            "transactions": self.transactions[:MAX_TRANSACTIONS_PER_BLOCK],
        }
        self.transactions = self.transactions[MAX_TRANSACTIONS_PER_BLOCK:]

        self.chain.append(block)

        with open("ledger.txt", "a") as f:
            if proof != 0:
                f.write("\n")
            f.write(json.dumps(block, indent=4) + ",")

        return block

    def get_previous_block(self):
        return self.chain[-1]  # last index of the chain

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(
                str(new_proof ** 2 - previous_proof ** 2).encode()
            ).hexdigest()
            if hash_operation[:4] == "0000":
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block["previous_hash"] != self.hash(previous_block):
                return False
            previous_proof = previous_block["proof"]
            proof = block["proof"]
            hash_operation = hashlib.sha256(
                str(proof ** 2 - previous_proof ** 2).encode()
            ).hexdigest()
            if hash_operation[:4] != "0000":
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transaction(self, sender, receiver, amount, signature):
        # verify transaction
        message = json.dumps({
            "sender": sender,
            "receiver": receiver,
            "amount": amount
        })

        if sender != "root":
            try:
                RSA.import_key(standardize_key(sender))
            except ValueError:
                raise ValueError("add_transaction: invalid sender")

            try:
                RSA.import_key(standardize_key(receiver))
            except ValueError:
                raise ValueError("add_transaction: invalid receiver")

            verify_signature(message, sender, signature)

            current_balance = self.get_balance(sender)["total"]
            print(sender)
            print(self.get_balance(sender))
            if current_balance < amount:
                raise ValueError("Not enough money.")

        # verified. add transaction
        self.transactions.append(
            {"sender": sender, "receiver": receiver, "amount": amount}
        )
        previous_block = self.get_previous_block()
        return previous_block["index"] + 1

    def get_balance(self, address):
        income = 0
        outcome = 0
        for block in self.chain:
            for transaction in block["transactions"]:
                if repr(transaction["sender"]) == repr(address):
                    outcome += transaction["amount"]
                if repr(transaction["receiver"]) == repr(address):
                    income += transaction["amount"]

        return {
            "total": income - outcome,
            "income": income,
            "outcome": outcome
        }

    def get_transactions(self, address):
        transactions = {
            "pending":  [],
            "success":  []
        }

        for block in self.chain:
            for transaction in block["transactions"]:
                sender = repr(transaction["sender"])
                receiver = repr(transaction["receiver"])
                if (sender == repr(address) or receiver == repr(address)):
                    transactions["success"].append(transaction)

        for transaction in self.transactions:
            print(transaction)
            sender = repr(transaction["sender"])
            receiver = repr(transaction["receiver"])
            if (sender == repr(address) or receiver == repr(address)):
                transactions["pending"].append(transaction)

        return transactions

    def add_node(self, address):
        if address not in self.nodes:
            with open("nodes.txt", "a") as f:
                self.nodes.add(address)
                f.write(address + "\n")

    def get_nodes(self):
        with open("nodes.txt", "r") as f:
            nodes = list(map(lambda line: line[:-1], f.readlines()))
        return nodes

    def replace_chain(self):
        network = self.get_nodes()
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f"http://{node}/get_chain")
            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
