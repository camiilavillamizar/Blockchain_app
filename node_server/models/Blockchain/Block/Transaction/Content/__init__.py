class Content():


    def __init__(self, text: str, name: str = None, email: str = None):
        self.name = name
        self.email = email
        self.text = text

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)