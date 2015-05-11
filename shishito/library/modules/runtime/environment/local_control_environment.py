from selenium import webdriver

from shishito.library.modules.runtime.environment.shishito_environment import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    def __init__(self):
        ShishitoEnvironment.__init__(self)
        self.platform_name = self.shishito_support.gid('test_platform')
        self.environment_name = self.shishito_support.gid('test_environment')
        self.config = self.shishito_support.get_environment_config(
            platform_name=self.platform_name,
            environment_name=self.environment_name)

    def start_driver(self, combination, capabilities):
        """ Starts driver """
        # add extensions to browser
        driver = None
        browser_profile = self.get_browser_profile(combination, capabilities)
        browser_type = capabilities['browser'].lower()

        # starts local browser
        if browser_type == "firefox":
            driver = webdriver.Firefox(browser_profile, capabilities=capabilities)
        elif browser_type == "chrome":
            driver = webdriver.Chrome(desired_capabilities=capabilities, chrome_options=browser_profile)
        elif browser_type == "ie":
            driver = webdriver.Ie(capabilities=capabilities)
        elif browser_type == "phantomjs":
            driver = webdriver.PhantomJS(desired_capabilities=capabilities)
        elif browser_type == "opera":
            driver = webdriver.Opera(desired_capabilities=capabilities)
            # SafariDriver bindings for Python not yet implemented
            # elif browser == "Safari":
            # self.driver = webdriver.SafariDriver()
        return driver

    def get_capabilities(self, combination):
        """Returns dictionary of capabilities for specific Browserstack browser/os combination """
        capabilities = {
            'acceptSslCerts': self.shishito_support.gid('accept_ssl_cert').lower() == 'false',
        }
        # TODO should not need to update capabilies for local webdriver
        # capabilities.update({
        #     'browser': self.config.get(combination, 'browser'),
        #     'browser_version': self.config.get(combination, 'browser_version'),
        #     'resolution': self.config.get(combination, 'resolution'),
        # })
        return capabilities

    def get_browser_profile(self, browser_type, capabilities):
        """ Returns updated browser profile ready to be passed to driver """
        profile = None

        # add extensions to remote driver
        if self.shishito_support.gid('with_extension'):
            # TODO add support for extensions again
            # browser_profile = self.add_extension_to_browser(browser_type, browser_profile)
            pass

        if browser_type == 'chrome':
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
            capabilities.update(chrome_options.to_capabilities())
        elif browser_type == 'firefox':
            profile = webdriver.FirefoxProfile()
        return profile