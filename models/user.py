from models.active_record_entity import ActiveRecordEntity

class User(ActiveRecordEntity):
    # __tablename__ = 'articles'

    
    _nickname = None
    _email = None
    _is_confirmed = None
    _role = None
    _password_hash = None
    _auth_token = None
    _created_at = None

    def get_nickname(self):
        return self._nickname
    
    def get_email(self):
        return self._email

    def get_role(self):
        return self._role

    def get_create_at(self):
        return self._create_at

    def get_password_hash(self):
        return self._password_hash

    def get_auth_token(self):
        return self._auth_token

    
    def set_author_id(self, author_id):
        self._author_id = author_id
    
    def set_nickname(self, nickname):
        self._nickname = nickname

    def set_email(self, email):
        self._email = email

    def set_role(self, role):
        self._role = role

    # def set_create_at(self, create_at):
    #     self._create_at = create_at

    @staticmethod
    def get_table_name():
        return 'user'
