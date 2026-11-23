import json
import secrets

from controller.controller import Controller
from exceptions import InvalidArgumentException
from models.article import Article


class ArticlesApiController(Controller):

    def send_json(self, response, data, status=200):
        response.status_code = status
        response.content_type = 'application/json'
        response.charset = 'utf-8'
        response.text = json.dumps(data, ensure_ascii=False)

    def article_to_dict(self, article):
        return {
            'id': article.get_id(),
            'author_id': article.get_author_id(),
            'name': article.get_name(),
            'text': article.get_text(),
            'img': article.get_img(),
            'create_at': article.get_create_at()
        }

    def check_api_csrf(self, request):
        token_cookie = request.cookies.get('csrf_token', '')
        token_header = request.headers.get('X-CSRF-Token', '')

        if not token_cookie or not token_header:
            return False

        return secrets.compare_digest(token_cookie, token_header)

    def check_user(self, response):
        if self.user is None:
            self.send_json(
                response,
                {'error': 'Необходимо авторизоваться.'},
                401
            )
            return False

        return True

    def check_owner(self, article, response):
        if not article.is_owned_by(self.user.get_id()):
            self.send_json(
                response,
                {'error': 'Можно изменять или удалять только свои статьи.'},
                403
            )
            return False

        return True

    def get_form_data(self, request):
        """
        WebOb может не разбирать request.POST для PATCH.
        На время чтения формы меняем метод на POST, затем восстанавливаем.
        Это позволяет получить поля и загруженный файл из multipart/form-data.
        """
        original_method = request.method

        if original_method in ('PATCH', 'PUT'):
            request.method = 'POST'
            try:
                return request.POST
            finally:
                request.method = original_method

        return request.POST

    def index(self, request, response):
        # GET /api/articles — список статей
        if request.method == 'GET':
            self.generate_csrf_token(response)

            articles = Article.find_all()

            self.send_json(
                response,
                {
                    'articles': [
                        self.article_to_dict(article)
                        for article in articles
                    ]
                }
            )
            return

        # POST /api/articles — создание статьи с изображением
        if request.method == 'POST':
            if not self.check_user(response):
                return

            if not self.check_api_csrf(request):
                self.send_json(
                    response,
                    {'error': 'Ошибка проверки CSRF-токена.'},
                    403
                )
                return

            try:
                form = self.get_form_data(request)

                name = (form.get('name') or '').strip()
                text = (form.get('text') or '').strip()
                img = form.get('img')

                if not name:
                    raise InvalidArgumentException(
                        'Укажите название статьи.'
                    )

                if not text:
                    raise InvalidArgumentException(
                        'Укажите текст статьи.'
                    )

                if img is None or not getattr(img, 'filename', '').strip():
                    raise InvalidArgumentException(
                        'Выберите изображение.'
                    )

                article = Article()
                article.set_author_id(self.user.get_id())
                article.set_name(name)
                article.set_text(text)

                # Сохраняем загруженное изображение.
                article.move_img_file(img)

                # Сохраняем статью.
                article.save()

                self.send_json(
                    response,
                    {
                        'message': 'Статья успешно создана.',
                        'article': self.article_to_dict(article)
                    },
                    201
                )

            except InvalidArgumentException as error:
                self.send_json(response, {'error': str(error)}, 400)

            return

        response.headers['Allow'] = 'GET, POST'
        self.send_json(
            response,
            {'error': 'Метод не поддерживается.'},
            405
        )

    def view(self, request, response, id):
        article = Article.get_by_id(id)

        if article is None:
            self.send_json(
                response,
                {'error': 'Статья не найдена.'},
                404
            )
            return

        # GET /api/articles/5 — просмотр статьи
        if request.method == 'GET':
            self.generate_csrf_token(response)
            self.send_json(
                response,
                {'article': self.article_to_dict(article)}
            )
            return

        # PATCH или PUT /api/articles/5 — изменение статьи
        # Поля и изображение передаются как multipart/form-data.
        if request.method in ('PATCH', 'PUT'):
            if not self.check_user(response):
                return

            if not self.check_owner(article, response):
                return

            if not self.check_api_csrf(request):
                self.send_json(
                    response,
                    {'error': 'Ошибка проверки CSRF-токена.'},
                    403
                )
                return

            try:
                form = self.get_form_data(request)

                name = form.get('name')
                text = form.get('text')
                img = form.get('img')

                if name is not None:
                    if not isinstance(name, str):
                        raise InvalidArgumentException(
                            'Название статьи должно быть текстом.'
                        )

                    name = name.strip()

                    if not name:
                        raise InvalidArgumentException(
                            'Название статьи не может быть пустым.'
                        )

                    article.set_name(name)

                if text is not None:
                    if not isinstance(text, str):
                        raise InvalidArgumentException(
                            'Текст статьи должен быть текстом.'
                        )

                    text = text.strip()

                    if not text:
                        raise InvalidArgumentException(
                            'Текст статьи не может быть пустым.'
                        )

                    article.set_text(text)

                # Если файл передан, заменяем изображение.
                # Если файл не передан, оставляем старое изображение.
                if img is not None and getattr(img, 'filename', '').strip():
                    article.move_img_file(img)

                article.save()

                self.send_json(
                    response,
                    {
                        'message': 'Статья успешно обновлена.',
                        'article': self.article_to_dict(article)
                    }
                )

            except InvalidArgumentException as error:
                self.send_json(response, {'error': str(error)}, 400)

            return

        # DELETE /api/articles/5 — удаление статьи
        if request.method == 'DELETE':
            if not self.check_user(response):
                return

            if not self.check_owner(article, response):
                return

            if not self.check_api_csrf(request):
                self.send_json(
                    response,
                    {'error': 'Ошибка проверки CSRF-токена.'},
                    403
                )
                return

            article.delete()

            self.send_json(
                response,
                {'message': 'Статья успешно удалена.'}
            )
            return

        response.headers['Allow'] = 'GET, PATCH, PUT, DELETE'
        self.send_json(
            response,
            {'error': 'Метод не поддерживается.'},
            405
        )