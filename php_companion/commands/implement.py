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
    def get_extended_symbol(self, view_content):
        search = re.search(r"extends\s+(\w+)", view_content)
        return search.group(1) if search else ''

    # Gets recursively locations
    #
    def get_locations(self, symbols, loop=0):
        locations = []
        for symbol in symbols:
            if symbol:
                locations += self.view.window().lookup_symbol_in_index(symbol)
                extended = []
                for location in locations:
                    extended.append(self.get_extended_symbol(open(location[0], 'r').read()))
                if len(extended) > 0:
                    locations += self.get_locations(extended, ++loop)
                if len(locations) > 0 and loop == 0:
                    break;
        return locations

    # Gets files with names that match the currently selected symbol
    #
    def get_matching_files(self):
        locations = self.get_locations([self.get_selected_symbol(), self.get_extended_symbol(self.get_view_content())])
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
