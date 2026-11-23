from views.view import View
from controller.controller import Controller
from models.article import Article
from models.user import User
from services.db import Db
import io
import os
import uuid
from PIL import Image, UnidentifiedImageError


from exceptions import (NotFoundException, UnauthorizedException,
                        FormValidationException, InvalidArgumentException)


class ArticlesController(Controller):
    

    def index(self, request, response):
        articles = Article.find_all()
        response.text = self.view.render_html('articles/articles.html', {'title' : 'MVC фреймворк ', 'h1' : 'Статья: ', 'articles' : articles })


    def api_page(self, request, response):
        response.text = self.view.render_html(
            'articles/api.html',
            {
                'title': 'Вывод через api',
                'h1': 'Вывод через api'
            }
        )


    # def about(self, request, response):
    #     response.text = self.view.render_html('site/about.html', {'title' : 'О нас', 'h1' : 'Вы на странице "о нас"'})

    def view(self, request, response, id):
        article = Article.get_by_id(id)
        if article is None:
            raise NotFoundException('Статья не найдена')

            
        user = User.get_by_id(article.get_author_id())

        response.text = self.view.render_html('articles/view.html', {'title' : f'MVC фреймворк - {article.get_name()}', 'h1' : f'Статья: {article.get_name()}', 'article' : article})


    ##обработка

    def edit(self, request, response, id):
        article = Article.get_by_id(id)

        if article is None:
            raise NotFoundException('Статья не найдена')

        if self.user is None:
            response.status_code = 401
            response.text = self.view.render_html(
                'errors/401.html'
            )
            return

        if not article.is_owned_by(self.user.get_id()):
            response.status_code = 403
            response.text = self.view.render_html(
                'errors/403.html'
            )
            return

        csrf_token = self.generate_csrf_token(response)

        if request.method == 'POST':
            if not self.validate_csrf_token(request):
                response.status_code = 403
                response.text = self.view.render_html(
                'errors/403.html'
                )
                return

            name = (request.POST.get('name') or '').strip()
            text = (request.POST.get('text') or '').strip()
            img = request.POST.get('img')

            form_error = None

            if not name:
                form_error = 'Введите название статьи.'
            elif not text:
                form_error = 'Введите описание статьи.'

            if form_error:
                response.status_code = 400
                response.text = self.view.render_html(
                    'articles/edit.html',
                    {
                        'title': f'Редактирование - {article.get_name()}',
                        'article': article,
                        'csrf_token': csrf_token,
                        'form_error': form_error,
                    }
                )
                return

            # Если новое изображение не выбрано, сохраняем прежнее.
            new_image_path = None

            try:
                if img is not None and getattr(img, 'filename', '').strip():
                    article.move_img_file(img)
                    filename = os.path.basename(article.get_img())
                    new_image_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'assets', 'uploads', filename
                    )

                article.set_name(name)
                article.set_text(text)
                article.save()

            except (InvalidArgumentException, ValueError) as error:
                if new_image_path and os.path.isfile(new_image_path):
                    try:
                        os.remove(new_image_path)
                    except OSError:
                        pass

                response.status_code = 400
                response.text = self.view.render_html(
                    'articles/edit.html',
                    {
                        'title': f'Редактирование - {article.get_name()}',
                        'article': article,
                        'csrf_token': csrf_token,
                        'form_error': str(error),
                    }
                )
                return

            except Exception:
                if new_image_path and os.path.isfile(new_image_path):
                    try:
                        os.remove(new_image_path)
                    except OSError:
                        pass

                raise

            response.status_code = 302
            response.headers = [
                ('Location', f'/articles/{article.get_id()}')
            ]
            return

        response.text = self.view.render_html(
            'articles/edit.html',
            {
                'title': f'Редактирование - {article.get_name()}',
                'article': article,
                'csrf_token': csrf_token,
            }
        )



    def _render_add_form(self, request, response, form_error=None, status_code=200,
                         name="", text=""):
        """Показывает форму создания статьи с сообщением об ошибке."""
        csrf_token = self.generate_csrf_token(response)
        response.status_code = status_code
        response.text = self.view.render_html(
            'articles/add.html',
            {
                'title': 'Новая статья',
                'h1': 'Создание статьи',
                'csrf_token': csrf_token,
                'form_error': form_error,
                'name': name,
                'text': text,
            }
        )

    def add(self, request, response):

        if self.user is None:
            self._render_add_form(
                request, response,
                'Для создания статьи необходимо войти в аккаунт.',
                status_code=401
            )
            return

        if request.method != 'POST':
            self._render_add_form(request, response)
            return

        # Ошибка CSRF также отображается на форме, но запрос отклоняется.
        if not self.validate_csrf_token(request):
            self._render_add_form(
                request, response,
                'Проверка безопасности не пройдена. Обновите страницу и попробуйте снова.',
                status_code=403
            )
            return

        name = (request.POST.get('name') or '').strip()
        text = (request.POST.get('text') or '').strip()
        img = request.POST.get('img')
        saved_image_path = None

        try:
            # Серверная проверка обязательных полей (HTML required недостаточно).
            if not name:
                raise FormValidationException('Укажите название статьи.')
            if not text:
                raise FormValidationException('Заполните описание статьи.')
            if img is None or not getattr(img, 'filename', '').strip():
                raise FormValidationException('Выберите изображение для статьи.')

            extension = os.path.splitext(img.filename)[1].lower()
            if extension not in ('.jpg', '.jpeg'):
                raise FormValidationException('Разрешены только JPG/JPEG-файлы.')

            max_file_size = 5 * 1024 * 1024
            raw_data = img.file.read(max_file_size + 1)

            if not raw_data:
                raise FormValidationException('Выбранный файл пустой.')
            if len(raw_data) > max_file_size:
                raise FormValidationException('Размер изображения не должен превышать 5 МБ.')

            # Проверяем не только расширение, но и фактическое содержимое файла.
            try:
                with Image.open(io.BytesIO(raw_data)) as image:
                    if image.format != 'JPEG':
                        raise FormValidationException(
                            'Файл не является настоящим JPEG-изображением.'
                        )
                    if image.width <= 0 or image.height <= 0:
                        raise FormValidationException('Некорректный размер изображения.')
                    if image.width * image.height > 20_000_000:
                        raise FormValidationException(
                            'Разрешение изображения слишком большое.'
                        )
                    image.verify()

                with Image.open(io.BytesIO(raw_data)) as image:
                    image.load()
                    safe_image = image.convert('RGB')
            except FormValidationException:
                raise
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
                raise FormValidationException(
                    'Изображение повреждено или имеет небезопасный формат.'
                )

            upload_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'assets', 'uploads'
            )
            os.makedirs(upload_dir, exist_ok=True)

            # Имя генерируется сервером, исходное имя файла не используется.
            filename = f'{uuid.uuid4().hex}.jpg'
            saved_image_path = os.path.join(upload_dir, filename)
            safe_image.save(saved_image_path, format='JPEG', quality=90, optimize=True)

            article = Article()
            article.set_author_id(self.user.get_id())
            article.set_name(name)
            article.set_text(text)
            article.set_img(f'/uploads/{filename}')
            article.save()

            response.status_code = 302
            response.headers = [('Location', f'/articles/{article.get_id()}')]
            return

        except (FormValidationException, InvalidArgumentException, ValueError) as error:
            # Удаляем изображение, если оно успело сохраниться, но статья не создалась.
            if saved_image_path and os.path.isfile(saved_image_path):
                try:
                    os.remove(saved_image_path)
                except OSError:
                    pass
            self._render_add_form(
                request, response, str(error), status_code=400,
                name=name, text=text
            )
            return
        except Exception:
            # Не раскрываем пользователю внутренние детали БД/сервера.
            print("Ошибка при создании статьи:")
            import traceback
            traceback.print_exc()
            if saved_image_path and os.path.isfile(saved_image_path):
                try:
                    os.remove(saved_image_path)
                except OSError:
                    pass
            self._render_add_form(
                request, response,
                'Не удалось создать статью из-за внутренней ошибки. Попробуйте ещё раз.',
                status_code=500, name=name, text=text
            )
            return

    
    def delete(self, request, response, id):
        article = Article.get_by_id(id)

        if article is None:
            raise NotFoundException('Статья не найдена')

        if self.user is None:
            response.status_code = 401
            response.text = 'Для удаления статьи необходимо войти в аккаунт.'
            return

        if not article.is_owned_by(self.user.get_id()):
            response.status_code = 403
            response.text = (
                'Недостаточно прав: удалять можно только собственные статьи.'
            )
            return

        if request.method != 'POST':
            response.status_code = 405
            response.text = 'Удаление допускается только методом POST.'
            return

        if not self.validate_csrf_token(request):
            response.status_code = 403
            response.text = 'Проверка безопасности не пройдена.'
            return

        article.delete()
        response.status_code = 302
        response.headers = [('Location', '/articles')]


    def search(self, request, response):                
        if not 'q' in request.GET:
            response.text = self.view.render_html('articles/search.html')
            return
        else:
            articles = Article.search_by_name(request.GET.get('q'))
            response.text = self.view.render_html('articles/search.html', {'q' : request.GET['q'], 'articles' : articles})
    
    


