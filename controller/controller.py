from views.view import View
from models.user_auth_service import UserAuthService
import secrets


class Controller:
    def __init__(self, request):
        self.layout = "default"
        self.view = View(self.layout)
        self.request = request

        if request.path.startswith('/api/'):
            # Для API используем HTTP Basic Authentication.
            authorization = request.headers.get('Authorization', '')
            self.user = UserAuthService.getUserByAuthBasic(authorization)
        else:
            # Для обычных страниц сайта оставляем авторизацию по cookie.
            token = request.cookies.get('token', '')
            self.user = UserAuthService.get_user_by_token(token)

        self.view.set_var('user', self.user)

    def generate_csrf_token(self, response):
        """Генерирует CSRF-токен и кладёт его в cookie."""
        token = self.request.cookies.get('csrf_token')

        if not token:
            token = secrets.token_hex(32)
            response.set_cookie(
                'csrf_token',
                token,
                httponly=False,
                samesite='Lax'
            )

        return token

    def validate_csrf_token(self, request):
        """Сравнивает CSRF-токен из формы с токеном из cookie."""
        token_from_form = request.POST.get('csrf_token')
        token_from_cookie = request.cookies.get('csrf_token')

        if not token_from_cookie or not token_from_form:
            return False

        return secrets.compare_digest(
            token_from_form,
            token_from_cookie
        )