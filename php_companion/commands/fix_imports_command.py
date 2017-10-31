import sublime
import sublime_plugin
import sys
from functools import reduce

from ..utils import find_symbol

class FixImportsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.window = self.view.window()
        file_name = self.view.file_name()

        if file_name.endswith('.php'):
            symbols = reduce(self.index_symbols_by_category, self.view.symbols(), {})
            # TODO make symbols (imports/references) unique
            self.imports = self.merge_symbols_for_categories(symbols, ['SU', 'SUA'])
            self.references = self.merge_symbols_for_categories(symbols, ['SP', 'SC', 'SCA', 'KA'])
            # print('imports', self.imports)
            # print('references', self.references)

            self.namespace = self.nextval(symbols.get('N'))
            self.klass = self.nextval(symbols.get('C'))

            for klass, use in self.imports.items():
                if not self.references.get(klass):
                    # print('removing use', klass, use)
                    region = self.view.find(('use ' + use.get('fqcn') + ';').replace('\\', '\\\\'), 0)
                    self.view.run_command('replace_fqcn', {'region_start': region.begin() -1, 'region_end': region.end(), 'namespace': '', 'leading_separator': False})

            self.references_iterator = iter(self.references.values())
            self.on_select()

    def on_select(self):
        try:
            reference = next(self.references_iterator)
            klass = reference.get('klass')
            if not self.imports.get(klass):
                self.symbols = find_symbol(klass, self.window)

                for symbol in self.symbols:
                    namespace = symbol[0]
                    if self.namespace and self.namespace.get('fqcn') in namespace:
                        return self.on_select()

                if len(self.symbols) == 1:
                    self.on_import(0)
                elif len(self.symbols) > 1:
                    sublime.set_timeout(lambda: self.window.show_quick_panel(self.symbols, self.on_import), 10)
            else:
                return self.on_select()
        except StopIteration:
            if self.view.is_dirty():
                self.view.run_command('save')
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise

    def on_import(self, index):
        if index == -1:
            return

        symbol = self.symbols[index]
        namespace = symbol[0]
        file = symbol[1]

        print('symbol', symbol, 'namespace', namespace, 'file', file)

        # if not namespace.replace('\\', '/') in file:
            # return

        # print('adding use', self.symbols[index][0])
        self.view.run_command('import_use', {'namespace': namespace})
        self.on_select()

    def index_symbols_by_category(self, carry, item):
        pos = item[0]
        begin = pos.begin()

        symbol = item[1]

        if not ':' in symbol:
            return carry

        chunks = symbol.split(':')
        category = chunks[0].lstrip()
        fqcn = chunks[1].lstrip()
        klass = fqcn.rsplit('\\', 1)[-1]

        # Handling traits usage
        if carry.get('C') and category == 'SU':
            category = 'SC'

        if not carry.get(category):
            carry[category] = {}

        if fqcn[0] != '\\' and self.view.substr(sublime.Region(begin - 1, begin)) != '\\':
            carry[category][klass] = {'fqcn': fqcn, 'klass': klass, 'pos': pos}

        return carry

    def merge_symbols_for_categories(self, symbols, categories):
        merged = {}
        for category in categories:
            if symbols.get(category):
                merged.update(symbols.get(category))
        return merged

    def nextval(self, obj):
        return next(iter(obj.values())) if type(obj) is dict else None

