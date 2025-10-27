from beanie import Document

class User(Document):
    username: str
    password_hash: str