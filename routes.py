from controller.site_controller import SiteController
# from controller.TestController import TestController
from controller.article_controller import ArticlesController

routes = {
    # "/home" :  [SiteController, SiteController.index],
    # "/about" :  [SiteController, SiteController.about],
    # "/test" :  [TestController, TestController.test],
    # "/test-action" :  [TestController, TestController.action],

    r"^/articles/(\d+)/edit$" : [ArticlesController, ArticlesController.edit],
    r"^/articles/(\d+)$" : [ArticlesController, ArticlesController.view],
    r"^/articles/(\d+)/delete$" : [ArticlesController, ArticlesController.delete],
    r"^/articles$" : [ArticlesController, ArticlesController.index],
    r"^/articles/add$" : [ArticlesController, ArticlesController.add],
    r"^/home$" : [SiteController, SiteController.index],
    r"^/about$" : [SiteController, SiteController.about],
    r"^/hello/(.*)$" : [SiteController, SiteController.hello],
}