"""This contains app entry point for running a demo site for this addon or running functional tests for this addon."""

# Pyramid
from pyramid.interfaces import IRequest

# Websauna
import websauna.system


class Initializer(websauna.system.DemoInitializer):
    """A demo / test app initializer for testing addon websauna.magiclogin."""

    def include_addons(self):
        """Include this addon in the configuration."""
        self.config.include("websauna.magiclogin")

    def configure_user(self):
        """Override default Websauna login system.

        We skip registration, forgot email and such functionality as it is not needed.
        """
        from websauna.magiclogin.requirelogin import DeferredActionLoginService
        from websauna.system.user import subscribers
        from websauna.system.user.credentialactivityservice import DefaultCredentialActivityService
        from websauna.system.user.interfaces import ICredentialActivityService
        from websauna.system.user.interfaces import ILoginService
        from websauna.system.user.interfaces import IRegistrationService
        from websauna.system.user.registrationservice import DefaultRegistrationService

        # Set up login service
        registry = self.config.registry
        registry.registerAdapter(factory=DeferredActionLoginService, required=(IRequest,), provided=ILoginService)
        registry.registerAdapter(factory=DefaultCredentialActivityService, required=(IRequest,), provided=ICredentialActivityService)
        registry.registerAdapter(factory=DefaultRegistrationService, required=(IRequest,), provided=IRegistrationService)

        # Set up user templates
        self.config.add_jinja2_search_path('websauna.magiclogin:templates', name='.html')
        self.config.add_jinja2_search_path('websauna.magiclogin:templates', name='.txt')
        self.config.add_jinja2_search_path('websauna.system.user:templates', name='.html')
        self.config.add_jinja2_search_path('websauna.system.user:templates', name='.txt')

        # Set up login event
        self.config.scan(subscribers)

        # Add the stock views we don't override
        self.config.add_view(view="websauna.system.user.views.login_social", route_name="login_social")
        self.config.add_route('logout', '/logout')
        self.config.add_view(view="websauna.system.user.views.logout", route_name="logout")

    def configure_static(self):
        """Configure static asset serving and cache busting."""
        super(Initializer, self).configure_static()
        self.config.registry.static_asset_policy.add_static_view('magiclogin-static', 'websauna.magiclogin:static')

    def configure_templates(self):
        super(Initializer, self).configure_templates()

        # Your app templates go here
        self.config.add_jinja2_search_path('websauna.magiclogin:demotemplates', name='.html', prepend=True)

    def configure_views(self):
        super(Initializer, self).configure_views()

        from websauna.magiclogin.tests import requireloginexamples
        self.config.scan(requireloginexamples)


def main(global_config, **settings):
    init = Initializer(global_config)
    init.run()
    return init.make_wsgi_app()
