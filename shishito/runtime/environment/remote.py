from __future__ import absolute_import

from selenium import webdriver

from shishito.runtime.environment.shishito import ShishitoEnvironment
from subprocess import call
from  subprocess import Popen,PIPE
import base64


class ControlEnvironment(ShishitoEnvironment):
    """ Remote control environment. """

    def call_browser(self, config_section):
        """ Starts browser """

        # get browser capabilities
        capabilities = self.get_capabilities(config_section)

        # get remote url
        remote_url = self.shishito_support.get_opt('remote_driver_url')

        # get driver
        return self.start_driver(capabilities, remote_url)

    def get_capabilities(self, config_section):
        """ Returns dictionary of capabilities for specific Browserstack browser/os combination """

        get_opt = self.shishito_support.get_opt

        return {
            'acceptSslCerts': get_opt('accept_ssl_cert').lower() == 'true',
            'browserName': get_opt(config_section, 'browser').lower(),
            'version': get_opt(config_section, 'browser_version'),
            'resolution': get_opt(config_section, 'resolution'),
            'javascriptEnabled': True,
            'chromeOptions': {
                "extensions": get_opt(config_section, 'with_extension')
            }
        }

    def start_driver(self, capabilities, remote_driver_url):
        """ Call remote browser (driver) """
        print("Starting remote driver", capabilities)
        if 'chromeOptions' in capabilities:

            ext_dir = capabilities['chromeOptions']["extensions"]

            with open(ext_dir, 'rb') as b:
                bytes = b.read()
                extension_bin = base64.b64encode(bytes)

            capabilities['chromeOptions']["extensions"] = [extension_bin.decode("utf-8")]
            driver = webdriver.Remote(command_executor=remote_driver_url, desired_capabilities=capabilities)

        if 'resolution' in capabilities:
            (width, height) = capabilities['resolution'].split('x')
            driver.set_window_size(width, height)

        return driver
