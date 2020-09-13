from database.helper import Database
class Content():


    def __init__(self, text: str, name: str = None, email: str = None, previous_name: str = None, previous_ip: str = None):
        self.name = name
        self.email = email
        self.text = text
        self.previous_name = previous_name
        self.previous_ip = previous_ip

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

    def save(self, transaction_id):
        sql = '''
        INSERT INTO content (text, name, email, previous_name, previous_ip, id_transaction)
        VALUES ("{0}","{1}","{2}", "{3}", "{4}", {5})
        '''.format(self.name, self.email, self.text, self.previous_name, self.previous_ip, transaction_id)
        database = Database()
        database.execute(sql)