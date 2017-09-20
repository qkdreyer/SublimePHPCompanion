import sublime
import sublime_plugin
import re
from functools import reduce

from ..settings import get_setting
from ..utils import find_symbol

class ImportUseListener(sublime_plugin.EventListener):
    def reduce_support(self, carry, item, tags):
        pos = item[0].begin()
        symbol = item[1]

        if type(tags) is not list:
            tags = [tags]

        for tag in tags:
            offset = len(tag)
            # print('symb:' + symbol[:offset], 'tag:' + tag)
            if symbol[:offset] == tag and not carry.get(symbol[offset:]) and self.view.substr(sublime.Region(pos - 1, pos)) != '\\':
                key = symbol[offset:].rsplit('\\', 1)[-1]
                carry[key] = item

        return carry

    def reduce_support_use(self, carry, item):
        return self.reduce_support(carry, item, '    SU: ')

    def reduce_support_class(self, carry, item):
        return self.reduce_support(carry, item, ['    SC: ', '    SCA: ', '    SE: '])

    def on_pre_save(self, view):
        self.view = view
        settings = sublime.load_settings('PHP Companion.sublime-settings')
        enable_import_use_on_save = settings.get('enable_import_use_on_save', False)
        file_name = view.file_name()

        if isinstance(enable_import_use_on_save, str):
            search = re.search(enable_import_use_on_save, file_name)
            enable_import_use_on_save = search != None

        if enable_import_use_on_save and file_name.endswith('.php'):
            symbols = view.symbols()
            uses = reduce(self.reduce_support_use, symbols, {})
            klasses = reduce(self.reduce_support_class, symbols, {})
            for klass in klasses:
                if not uses.get(klass):
                    self.namespaces = find_symbol(klass, view.window())
                    print('klass', klass, self.namespaces)

                    if len(self.namespaces) == 1:
                        self.on_done(0)
                    elif len(self.namespaces) > 1:
                        view.window().show_quick_panel(self.namespaces, self.on_done)

    def on_done(self, index):
        if index == -1:
            return

        self.view.run_command("import_use", {"namespace": self.namespaces[index][0]})
