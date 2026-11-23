import io
import os
import uuid

from PIL import Image, UnidentifiedImageError

from exceptions import InvalidArgumentException
from models.active_record_entity import ActiveRecordEntity
from models.user import User


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 МБ
MAX_IMAGE_PIXELS = 20_000_000


class Article(ActiveRecordEntity):
    _author_id = None
    _name = None
    _text = None
    _create_at = None
    _img = None

    def get_author_id(self):
        return self._author_id

    def is_owned_by(self, user_id):
        """Проверяет, принадлежит ли статья указанному пользователю."""
        return (
            self._author_id is not None
            and user_id is not None
            and str(self._author_id) == str(user_id)
        )

    def get_name(self):
        return self._name

    def get_text(self):
        return self._text

    def get_img(self):
        return self._img

    def get_create_at(self):
        return self._create_at

    def get_author(self):
        return User.get_by_id(self._author_id)

    def set_author_id(self, author_id):
        self._author_id = author_id

    def set_name(self, name):
        self._name = name

    def set_text(self, text):
        self._text = text

    def set_img(self, img):
        self._img = img

    def save(self):
        """Не позволяет сохранить статью без обязательных данных."""
        if not isinstance(self._name, str) or not self._name.strip():
            raise InvalidArgumentException('Укажите название статьи.')

        if not isinstance(self._text, str) or not self._text.strip():
            raise InvalidArgumentException('Заполните описание статьи.')

        if not isinstance(self._img, str) or not self._img.strip():
            raise InvalidArgumentException('Выберите изображение для статьи.')

        super().save()

    @staticmethod
    def create(fields, img_file, author):
        """Создаёт статью из полей формы и загруженного изображения."""
        article = Article()
        article.validate(fields, img_file)

        article._name = fields['name'].strip()
        article._text = fields['text'].strip()
        article._author_id = author.get_id()

        if img_file is not None and getattr(img_file, 'filename', '').strip():
            article.move_img_file(img_file)
        else:
            # Запасное изображение должно находиться в assets/uploads.
            article._img = '/uploads/default.jpg'

        article.save()
        return article

    def updateFromArray(self, fields, img_file=None):
        """Обновляет поля статьи и, если передан, изображение."""
        self.validate(fields, img_file)

        self._name = fields['name'].strip()
        self._text = fields['text'].strip()

        if img_file is not None and getattr(img_file, 'filename', '').strip():
            self.move_img_file(img_file)

        self.save()
        return self

    @staticmethod
    def search_by_name(search_string):
        return Article.search('name', search_string)

    def validate(self, fields, img_file=None):
        name = fields.get('name')
        text = fields.get('text')

        if not isinstance(name, str) or not name.strip():
            raise InvalidArgumentException('Укажите название статьи.')

        if not isinstance(text, str) or not text.strip():
            raise InvalidArgumentException('Заполните описание статьи.')

    def move_img_file(self, img_file):
        """Проверяет JPEG-файл, сохраняет его и записывает путь в статью."""
        if img_file is None or not getattr(img_file, 'filename', '').strip():
            raise InvalidArgumentException('Выберите изображение для статьи.')

        extension = os.path.splitext(img_file.filename)[1].lower()
        if extension not in ('.jpg', '.jpeg'):
            raise InvalidArgumentException('Разрешены только JPG/JPEG-файлы.')

        try:
            img_file.file.seek(0)
            raw_data = img_file.file.read(MAX_FILE_SIZE + 1)
        except (AttributeError, OSError, ValueError):
            raise InvalidArgumentException('Не удалось прочитать файл изображения.')

        if not raw_data:
            raise InvalidArgumentException('Выбранный файл пустой.')

        if len(raw_data) > MAX_FILE_SIZE:
            raise InvalidArgumentException(
                'Размер изображения не должен превышать 5 МБ.'
            )

        try:
            # Сначала проверяем, что файл действительно является JPEG.
            with Image.open(io.BytesIO(raw_data)) as image:
                if image.format != 'JPEG':
                    raise InvalidArgumentException(
                        'Файл не является настоящим JPEG-изображением.'
                    )

                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise InvalidArgumentException(
                        'Разрешение изображения слишком большое.'
                    )

                image.verify()

            # Повторно открываем и перекодируем изображение перед сохранением.
            with Image.open(io.BytesIO(raw_data)) as image:
                image.load()
                safe_image = image.convert('RGB')

        except InvalidArgumentException:
            raise
        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
            Image.DecompressionBombError
        ):
            raise InvalidArgumentException(
                'Изображение повреждено или имеет неподдерживаемый формат.'
            )

        project_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        upload_dir = os.path.join(project_dir, 'assets', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        filename = f'{uuid.uuid4().hex}.jpg'
        disk_path = os.path.join(upload_dir, filename)

        try:
            safe_image.save(
                disk_path,
                format='JPEG',
                quality=90,
                optimize=True
            )
        except OSError:
            raise InvalidArgumentException(
                'Не удалось сохранить изображение на сервере.'
            )

        self._img = f'/uploads/{filename}'

    @staticmethod
    def check_file_size(file_item, max_size):
        """Проверяет размер файла, не загружая его целиком в память."""
        try:
            current_pos = file_item.file.tell()
            file_item.file.seek(0)

            total_size = 0
            chunk_size = 8192

            while True:
                chunk = file_item.file.read(chunk_size)
                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_size:
                    break

            file_item.file.seek(current_pos)
            return total_size <= max_size, total_size

        except (AttributeError, OSError, ValueError):
            return False, 0

    @staticmethod
    def get_table_name():
        return 'articles'