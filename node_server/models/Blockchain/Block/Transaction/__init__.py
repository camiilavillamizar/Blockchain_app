from models.Blockchain.Block.Transaction.Content import Content
from typing import List

class Transaction():
    def __init__(self, type: str, content: List[Content], user_name: str, IP: str, datetime: str):
        self.content = Content.from_json(content)
        self.type = type
        self.user_name = user_name
        self.IP = IP
        self.datetime = datetime

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

    def __repr__(self):
        return f'<Transaction> {self.content}'
    