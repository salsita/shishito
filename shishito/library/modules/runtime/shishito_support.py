import ConfigParser
import os
from importlib import import_module

import pytest


class ShishitoSupport(object):
    def __init__(self):
        self.project_root = os.getcwd()
        self.configs = self.load_configs()
        self.config = ConfigParser.RawConfigParser()

    def load_configs(self):
        """ Loads variables from .properties configuration files,  check if project didn't contain such folder
        (for non selenium projects) """
        config_path = os.path.join(self.project_root, 'config')
        config = ConfigParser.ConfigParser()
        if os.path.exists(config_path):
            # load server config variables
            server_config = os.path.join(config_path, 'server_config.properties')
            config.read(server_config)
            server_config_vars = dict(config.defaults())
            # load local config variables
            local_config = os.path.join(config_path, 'local_config.properties')
            config.read(local_config)
            local_config_vars = dict(config.defaults())
            # load non selenium config variables
            non_selenium_config = os.path.join(config_path, 'non_selenium_config.properties')
            config.read(non_selenium_config)
            non_selenium_config = dict(config.defaults())
            return_configs = [server_config_vars, local_config_vars, non_selenium_config]
            return return_configs

    def gid(self, key):
        """ Gets value from config variables based on provided key.
         If local execution parameter is "True", function will try to search for parameter in local configuration file.
         If such parameter is not found or there is an error while reading the file, server (default) configuration
         file will be used instead. """
        if not self.configs:
            return None

        # first try to lookup pytest config
        try:
            value = pytest.config.getoption(key)
            if value:
                return value
            else:
                use_logs = True
        except (ValueError, AttributeError):
            use_logs = True
        # lookup value from config files
        if use_logs:
            server_config = self.configs[0]
            local_config = self.configs[1]
            configs = []
            if local_config.get('local_execution').lower() == 'true':
                configs.append((local_config, 'local config'))
            configs.extend([(server_config, 'server config'), (os.environ, 'env variables')])
            for idx, cfg in enumerate(configs):
                if key in cfg[0] and cfg[0][key] != '':
                    # if idx:
                    # print "%s not found in %s, using value from %s" % (key, configs[0][1], cfg[1])
                    return cfg[0][key]
                    # print "%s not found in any config" % key

    def get_modules(self, platform_module_name, environment_module_name):
        platform_path = 'shishito.library.modules.runtime.platform.' + platform_module_name + '.control_execution'
        environment_path = 'shishito.library.modules.runtime.environment.' + environment_module_name + '.environment_control'
        return {'platform': getattr(import_module(platform_path), 'ControlExecution'),
                'environment': getattr(import_module(environment_path), 'ControlEnvironment')}