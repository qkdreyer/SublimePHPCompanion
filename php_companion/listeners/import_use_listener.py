import sublime
import sublime_plugin
import re
from functools import reduce

from ..settings import get_setting
from ..utils import find_symbol

class ImportUseListener(sublime_plugin.EventListener):
    def index_symbols_by_category(self, carry, item):
        pos = item[0]
        begin = pos.begin()

        symbol = item[1]
        chunks = symbol.split(':')
        category = chunks[0].lstrip()
        klass = chunks[1].lstrip()

        if not carry.get(category):
            carry[category] = {}

        if not carry[category].get(klass) and self.view.substr(sublime.Region(begin - 1, begin)) != '\\':
            key = klass.rsplit('\\', 1)[-1]
            carry[category][key] = [klass, pos]

        return carry

    def merge_symbols_for_categories(self, symbols, categories):
        merged = {}
        for category in categories:
            if symbols.get(category):
                merged.update(symbols.get(category))
        return merged

    def on_pre_save(self, view):
        self.view = view
        settings = sublime.load_settings('PHP Companion.sublime-settings')
        enable_import_use_on_save = settings.get('enable_import_use_on_save', False)
        file_name = view.file_name()

        if isinstance(enable_import_use_on_save, str):
            search = re.search(enable_import_use_on_save, file_name)
            enable_import_use_on_save = search != None

        if enable_import_use_on_save and file_name.endswith('.php'):
            symbols = reduce(self.index_symbols_by_category, view.symbols(), {})
            self.namespace = list(symbols.get('N').items())[0][1][0]
            uses = self.merge_symbols_for_categories(symbols, ['SU', 'SUA'])
            klasses = self.merge_symbols_for_categories(symbols, ['SC', 'SCA', 'SE'])
            print('symbols', symbols)

            for klass in klasses:
                if not uses.get(klass):
                    print('adding klass', klass, klasses[klass])
                    self.namespaces = find_symbol(klass, view.window())

                    if len(self.namespaces) == 1:
                        self.on_done(0)
                    elif len(self.namespaces) > 1:
                        view.window().show_quick_panel(self.namespaces, self.on_done)

            for use in uses:
                if not klasses.get(use):
                    print('removing use', use, uses[use])
                    region = uses[use][1]
                    self.view.run_command("replace_fqcn", {"region_start": region.begin() - 5, "region_end": region.end() + 1, "namespace": ''})

    def on_done(self, index):
        if index == -1:
            return

        namespace = self.namespaces[index][0]
        if not self.namespace in namespace:
            self.view.run_command("import_use", {"namespace": namespace})
