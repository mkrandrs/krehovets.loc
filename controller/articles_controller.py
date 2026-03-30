from views.view import View
from controller.controller import Controller
from models.article import Article
from services.db import Db

class ArticlesController(Controller):
    

    def index(self, request, response):
        articles = Article.find_all(Article)
        print(articles)
        response.text = self.view.render_html('articles/articles.html', {'title' : 'MVC фреймворк ', 'h1' : 'Статья: ', 'articles' : articles})

    # def about(self, request, response):
    #     response.text = self.view.render_html('site/about.html', {'title' : 'О нас', 'h1' : 'Вы на странице "о нас"'})

    def view(self, request, response, id):
        article = Article.get_by_id(id, Article)
        print(article.name, article.text)
        response.text = self.view.render_html('articles/view.html', {'title' : f'MVC фреймворк - {article.name}', 'h1' : f'Статья: {article.name}', 'article' : article})