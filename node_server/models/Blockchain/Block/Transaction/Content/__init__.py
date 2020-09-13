from database.helper import Database
class Content():


    def __init__(self, text: str, name: str = None, email: str = None):
        self.name = name
        self.email = email
        self.text = text

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

    def save(self, transaction_id):
        sql = '''
        INSERT INTO content (text, name, email, id_transaction)
        VALUES ("{0}","{1}","{2}",{3})
        '''.format(self.name, self.email, self.text, transaction_id)
        database = Database()
        database.execute(sql)