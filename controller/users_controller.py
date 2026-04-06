from controller.controller import Controller
from models.user import User
from exceptions import NotFoundException

class UsersController(Controller):
    

    def sign_up(self, request, response):

        if  request.method == 'POST':
            print(request.POST)
            return
        
        response.text = self.view.render_html('users/sign_up.html', {'title' : 'MVC фреймворк '})

    # def about(self, request, response):
    #     response.text = self.view.render_html('site/about.html', {'title' : 'О нас', 'h1' : 'Вы на странице "о нас"'})

 
    


