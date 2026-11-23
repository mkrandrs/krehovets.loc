import json
import os
import re
from models.user_auth_service import UserAuthService

from controller.site_controller import SiteController
from exceptions import NotFoundException
from views.view import View
from webob import Request, Response
from exceptions import UnauthorizedException, InvalidMethodException


from whitenoise import WhiteNoise

import routes
import handlers




class API:
    def __init__(self, static_dir="assets"):
        self.routes = routes.routes


        ##защита img

        self.whitenoise = WhiteNoise(
            self.wsgi_app,
            root=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                static_dir
            ),
            autorefresh=True
        )

    def wsgi_app(self, environ, start_response):
        request = Request(environ)

        response = self.handle_request(request)

        return response(environ, start_response)
    
    def __call__(self, environ, start_response):
        # requet = Request(environ)
        # response = self.handle_request(requet)
        # return response(environ, start_response)
        return self.whitenoise(environ, start_response)




        

        # response_body  = ['{key}: {value}'.format(key=key, value=value) for key, value in sorted(environ.items())]
        
        # response.text = '\n'.join(response_body)
        # response.headers.add('Content-type', 'text/plain')

        
        
        
        # status = "200 OK"



        # response_headers = [('Content-type', 'text/plain')]
        # start_response(status, response_headers)

        # return [response_body.encode('utf-8')]

    def handle_request(self, request):
        response = Response()

        controller = SiteController(request)

        api = False

        # method = request.method
        # if isinstance(handler[1], dict):
        #     api = True
        #     if method in handler[1]:
        #         action = handler[1][method]
        #     else:
        #         raise InvalidMethodException('Method not support')
        # else:
        #     action = handler[1]

        try:
            result = self.find_handler_re(request_path=request.path)

            request_url = request.environ.get("REQUEST_URI")

            result = self.find_handler_re(request_path=request.path)
            if result is None:
                raise NotFoundException('Страница не найдена')

            handler, params = result

            # ИСПРАВЛЕНО: Для создания контроллера берем первый элемент из списка handler[0]
            controller = handler[0](request)

            method = request.method
            # ИСПРАВЛЕНО: Для проверки словаря методов берем второй элемент handler[1]
            if isinstance(handler[1], dict):
                api = True
                if method in handler[1]:
                    action = handler[1][method]
                else:
                    raise InvalidMethodException('Method not support')
            # ИСПРАВЛЕНО: Если handler[1] это не словарь, а строка/функция (обычный роут)
            else:
                action = handler[1]

            controller = handler[0](request)

            # Для API пользователя определяем по заголовку Authorization: Basic ...
            if request.path.startswith('/api/'):
                controller.user = UserAuthService.getUserByAuthBasic(
                    request.headers.get('Authorization')
                )

                # GET доступен всем. Остальные методы требуют действительные учётные данные.
                if request.method != 'GET' and controller.user is None:
                    response.status_code = 401
                    response.headers['WWW-Authenticate'] = (
                        'Basic realm="API", charset="UTF-8"'
                    )
                    response.content_type = 'application/json'
                    response.charset = 'utf-8'
                    response.text = json.dumps(
                        {'error': 'Необходимо авторизоваться.'},
                        ensure_ascii=False
                    )
                    return response

            action(controller, request, response, *params)


        except NotFoundException as e:
            response.status_code = 404
            response.text = View('default').render_html('errors/404.html', {'error': e})

        except UnauthorizedException as e:
            response.status_code = 401
            response.text = View('default').render_html('errors/401.html', {'error': e})

        except InvalidMethodException as e:
            response.status_code = 405
            if api:
                # ИСПРАВЛЕНО: Опечатка display_jso -> display_json
                response.text = controller.view.display_json({'error': str(e)})
            else:
                response.text = controller.view.render_html('errors/405.html', {'error': e})

        return response

    def find_handler(self, request_path):
        for path, handler in self.routes.items():
            if path == request_path:
                return handler
            
    def find_handler_re(self, request_path):
        for path, handler in self.routes.items():
            match = re.search(path, request_path)
            if match is not None:
                return handler, match.groups()
    
    def default_response(self, response):
        response.status_code = 404
        response.text = "Page is not found"
    
    def route(self, path):
        def wrapper(handler):
            self.routes[path] = handler
            return handler
        return wrapper


app = API()



# def app (environ, start_response):
