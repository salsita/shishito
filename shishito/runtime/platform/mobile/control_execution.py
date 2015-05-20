from shishito.runtime.platform.shishito_execution import ShishitoExecution


class ControlExecution(ShishitoExecution):
    """ ControlExecution for mobile platform"""

    def get_test_result_prefix(self, config_section):
        platform = self.shishito_support.get_opt(config_section, 'platformName')
        platform_version = self.shishito_support.get_opt(config_section, 'platformVersion')

        return '[%s, %s, %s]' % (config_section, platform, platform_version)
