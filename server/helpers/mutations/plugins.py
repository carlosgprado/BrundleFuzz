#
# Plugin Loader
# Keep it simple, stupid:
# https://lkubuntu.wordpress.com/2012/10/02/writing-a-python-plugin-api/
#

import imp
import os


class Plugins(object):
    def __init__(self, parent):
        self.plugin_folder = './plugins'
        self.main_module = '__init__'
        self.parent = parent
        self.cfg = parent.cfg
        
    def get_plugins(self):
        plugins = []
        possible_plugins = os.listdir(self.plugin_folder)

        for p in possible_plugins:
            # Plugins must be explicitly selected
            # in the config.ini file
            try:
                pc = self.cfg.getboolean('plugins', p)
                if pc:
                    print "Found configured plugin: %s" % p

                else:
                    continue

            except:
                # Option not defined in config file
                continue

            location = os.path.join(self.plugin_folder, p)
            if not os.path.isdir(location) or not self.main_module + '.py' in os.listdir(location):
                continue
            info = imp.find_module(self.main_module, [location])
            plugins.append({'name': p, 'info': info})

        return plugins

    def load_plugin(self, plugin):
        return imp.load_module(self.main_module, *plugin['info'])
