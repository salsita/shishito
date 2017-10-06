from __future__ import absolute_import

from selenium import webdriver

from shishito.runtime.environment.shishito import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    """ Remote control environment. """

    def call_browser(self, config_section):
        """ Starts browser """

        # get browser capabilities
        capabilities = self.get_capabilities(config_section)

        # get remote url
        remote_url = self.shishito_support.get_opt('remote_driver_url')

        # get driver
        browser_type = self.shishito_support.get_opt(config_section, 'browser').lower()
        return self.start_driver(browser_type, capabilities, remote_url, config_section)



    def start_driver(self, browser_type, capabilities, remote_driver_url, config_section):
        """ Call remote browser (driver) """
        try:
            extensions = capabilities['chromeOptions']['extensions']    # do not print the huge base64 extension content
            capabilities['chromeOptions']['extensions'] = ['...']
            print("Starting remote driver", capabilities)
            capabilities['chromeOptions']['extensions'] = extensions
        except:
            print("Starting remote driver", capabilities)

        browser_profile = self.get_browser_profile(browser_type, capabilities, config_section)
        driver = webdriver.Remote(
            command_executor=remote_driver_url,
            desired_capabilities=capabilities,
            browser_profile=browser_profile)

        if 'resolution' in capabilities:
            (width, height) = capabilities['resolution'].split('x')
            driver.set_window_size(width, height)

        return driver
