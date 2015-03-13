from shishito.library.modules.runtime.shishito_support import ShishitoSupport


class ShishitoEnvironment(object):
    def __init__(self):
        self.shishito_support = ShishitoSupport()
        self.capabilities = None

    def call_browser(self, combination, capabilities=None):
        """ Starts browser """
        # get browser capabilities and profile
        if capabilities:
            capabilities.update(self.get_capabilities(combination))
        else:
            capabilities = self.get_capabilities(combination)
        return self.start_driver(combination, capabilities)

    def get_capabilities(self, combination):
        """ Returns dictionary of browser capabilities """
        pass

    def start_driver(self, combination, capabilities):
        """ Starts driver """
        pass

    def get_browser_profile(self, browser_type, capabilities):
        """ Returns updated browser profile ready to be passed to driver """
        pass