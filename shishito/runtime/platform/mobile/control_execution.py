from shishito.runtime.platform.shishito_execution import ShishitoExecution


class ControlExecution(ShishitoExecution):
    """ ControlExecution for mobile platform"""

    def get_test_result_prefix(self, config_section):
        """ Create string prefix for test results.

        :param str config_section: section in platform/environment.properties config
        :return: str with test result prefix
        """

        platform = self.shishito_support.get_opt(config_section, 'platformName')
        platform_version = self.shishito_support.get_opt(config_section, 'platformVersion')

        return '[%s, %s, %s]' % (config_section, platform, platform_version)
