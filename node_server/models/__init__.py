from datetime import datetime
from hashlib import sha256
from typing import List
import jsons
from node_server import db


class Content(db.Model):
    id: int
    name: str
    email: str
    text: str
    previous_name: str
    previous_ip: str
    transaction: str

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), index=False, unique=False, nullable=False)
    email = db.Column(db.String(180), index=False, unique=False, nullable=True)
    text = db.Column(db.String(180), index=False, unique=False, nullable=False)
    previous_name = db.Column(db.String(180), index=False,
                              unique=False, nullable=True)
    previous_ip = db.Column(db.String(180), index=False,
                            unique=False, nullable=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))

    def __init__(self, text: str = None, name: str = None, email: str = None, previous_name: str = None, previous_ip: str = None):
        self.name = name
        self.email = email
        self.text = text
        self.previous_name = previous_name
        self.previous_ip = previous_ip
    
    @property
    def serialize(self):
        return {
            'name': self.name,
            'email': self.email,
            'text': self.text,
            'previous_name': self.previous_name,
            'previous_ip': self.previous_ip,
        }

class Transaction(db.Model):
    id: int
    __type: str
    user_name: str
    ip: str
    datetime: str
    content: Content

    id = db.Column(db.Integer, primary_key=True)
    __type = db.Column(db.String(180), index=False, unique=False, nullable=False)
    user_name = db.Column(db.String(180), index=False,
                          unique=False, nullable=False)
    ip = db.Column(db.String(180), index=False, unique=False, nullable=False)
    datetime = db.Column(db.String(180), nullable=False)
    

    def __init__(self, type: str = None, content: Content = {}, user_name: str = None, IP: str = None, datetime: str = None):
        self.content = Content(**content)
        self.__type = type
        self.user_name = user_name
        self.ip = IP
        self.datetime = datetime

    def __repr__(self):
        return f'<Transaction> {self.content}'

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self,type):
        self.__type = type
    
    @property
    def serialize(self):
        return {
            'type': self.type,
            'user_name': self.user_name,
            'IP': self.ip,
            'datetime': self.datetime,
            'content': self.content.serialize,
        }

class Block:
    index: int
    transactions: Transaction
    datetime: str
    previous_hash: str
    nonce: int

    def __init__(self, index, transactions: Transaction, datetime, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.datetime = datetime
        self.previous_hash = previous_hash
        self.nonce = nonce

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        block_string = jsons.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()
    
    @property
    def serialize(self):
        return {
            'index': self.index,
            'transactions': [i.serialize for i in self.transactions if isinstance(i,Transaction)],
            'datetime': self.datetime,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
        }

class Blockchain:
    # difficulty of our PoW algorithm
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        for transaction in block.transactions:
            print(transaction.__dict__,flush=True)
            db.session.add(transaction)
            db.session.commit()
        return True

    @staticmethod
    def proof_of_work(block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction: Transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            # remove the hash field to recompute the hash again
            # using `compute_hash` method.
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block_hash) or \
                    previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          datetime=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []

        return (new_block, proof)
