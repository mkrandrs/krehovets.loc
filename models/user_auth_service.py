import base64
import binascii

from models.user import User
from werkzeug.security import check_password_hash


class UserAuthService:

    @staticmethod
    def create_token(user):
        return str(user.get_id()) + ':' + user.get_auth_token()

    @staticmethod
    def get_user_by_token(token):
        if not token:
            return None

        try:
            user_id, auth_token = token.split(':', 1)
            user = User.get_by_id(int(user_id))
        except (ValueError, TypeError):
            return None

        if user is None or user.get_auth_token() != auth_token:
            return None

        return user

    @staticmethod
    def getUserByAuthBasic(authorization_header):
        if not authorization_header:
            return None

        try:
            scheme, encoded_credentials = authorization_header.split(None, 1)

            if scheme.lower() != 'basic':
                return None

            credentials = base64.b64decode(
                encoded_credentials,
                validate=True
            ).decode('utf-8')

            # Формат: nickname:password
            # Разделяем по первому двоеточию, чтобы пароль мог содержать двоеточия.
            nickname, password = credentials.split(':', 1)

        except (
            ValueError,
            UnicodeDecodeError,
            binascii.Error
        ):
            return None

        if not nickname or not password:
            return None

        user = User.find_one_by_column('nickname', nickname)

        if user is None:
            return None

        if not check_password_hash(user.get_password_hash(), password):
            return None

        return user