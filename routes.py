from controller.site_controller import SiteController

routes = {
    "/home" :  [SiteController, SiteController.index],
    "/about" :  [SiteController, SiteController.about],
}