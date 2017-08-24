import sublime
import sublime_plugin
import re

class ImplementCommand(sublime_plugin.TextCommand):

    # Gets the currently selected symbol
    #
    def get_selected_symbol(self):
        point = self.view.sel()[0]
        region = self.view.word(point)
        return self.view.substr(region)

    # Gets the current view content
    #
    def get_view_content(self):
        size = self.view.size()
        region = sublime.Region(0, size)
        return self.view.substr(region)

    # Gets the extended symbol
    #
    def get_extended_symbol(self):
        view_content = self.get_view_content()
        search = re.search(r"extends\s+(\w+)", view_content)
        return search.group(1) if search else ''

    # Gets files with names that match the currently selected symbol
    #
    def get_matching_files(self):
        window = self.view.window()
        symbols = [self.get_selected_symbol, self.get_extended_symbol]
        locations = None

        for symbol in symbols:
            symbol = symbol()
            if symbol:
                locations = self.view.window().lookup_symbol_in_index(symbol)
                if locations:
                    break

        return list(map(lambda x: x[0], locations)) if locations else []

    # Handles the selection of a quick panel item
    #
    def on_done(self, index):
        if index == -1:
            return

        self.view.run_command("parse", {"path": self.files[index]})

    # Runs the plugin
    #
    def run(self, edit):
        self.files = self.get_matching_files()

        if (len(self.files) == 1):
            self.view.run_command("parse", {"path": self.files[0]})

        if (len(self.files) > 1):
            self.view.window().show_quick_panel(self.files, self.on_done)
