from controller.site_controller import SiteController
from controller.TestController import TestController
from controller.articles_controller import ArticlesController

routes = {
    # "/home" :  [SiteController, SiteController.index],
    # "/about" :  [SiteController, SiteController.about],
    # "/test" :  [TestController, TestController.test],
    # "/test-action" :  [TestController, TestController.action],

    r"^/articles/(\d+)$" : [ArticlesController, ArticlesController.view],
    r"^/articles$" : [ArticlesController, ArticlesController.index],
    r"^/home$" : [SiteController, SiteController.index],
    r"^/about$" : [SiteController, SiteController.about],
    r"^/hello/(.*)$" : [SiteController, SiteController.hello],
}