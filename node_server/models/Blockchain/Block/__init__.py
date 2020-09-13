from hashlib import sha256
import jsons
from models.Blockchain.Block.Transaction import Transaction


class Block:
    def __init__(self, index, transactions: Transaction, datetime, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.datetime = datetime
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        block_string = jsons.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()