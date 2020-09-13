from models.Blockchain.Block.Transaction.Content import Content
from typing import List
from database.helper import Database


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

    def save(self):
        sql = '''
            INSERT INTO "main"."transactions"("type","user_name","IP","datetime") VALUES ("{0}","{1}","{2}","{3}");
        '''.format(self.type, self.user_name, self.IP, self.datetime)
        database = Database()
        
        transaction_id = database.execute(sql)
        print(type(self.content), flush=True)
        if(isinstance(self.content, Content)):
            self.content.save(transaction_id)
        else:
            for content in self.content:
                content.save(transaction_id)
