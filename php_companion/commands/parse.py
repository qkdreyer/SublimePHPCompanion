import sublime
import sublime_plugin
import re

from ..settings import get_setting

METHOD_PATTERN = "(?<!\* )(?:abstract )?((?:public|protected|private)(?: static)?\s+function\s+[\w]+\s*\(.*?\)(?:\s*\:\s*\w+)?)\s*(?:;|{)"
CLASS_PATTERN = "(interface|abstract([A-Z0-9\s]+)class)\s+[A-Z0-9]+"
METHOD_TEMPLATE = "\n\t{0}\n\t{{\n\t\t{1}\n\t}}\n"

class ParseCommand(sublime_plugin.TextCommand):

    # Normalizes a given path to the current system style
    # -- This method is from the PHP Companion utils file
    #
    def normalize_to_system_style_path(self, path):
        if sublime.platform() == "windows":
            path = re.sub(r"/([A-Za-z])/(.+)", r"\1:/\2", path)
            path = re.sub(r"/", r"\\", path)
        return path

    # Find methods and parse docblocks
    #
    def get_methods(self, content):
        methods = [{"method": "Insert all methods", "docblock": None}]
        for method in re.findall(METHOD_PATTERN, content, re.S):
            pos = content.index(method)
            try:
                end = content.rindex("*/", 0, pos)
                if (re.findall(METHOD_PATTERN, content[end:pos], re.S)
                    or re.findall(CLASS_PATTERN, content[end:pos])):
                        docblock = None
                else:
                    start = content.rindex("/**", 0, end)
                    docblock = content[start:end + 2]
            except ValueError:
                docblock = None

            methods.append({"method": method, "docblock": docblock})
        return methods

    # Runs the plugin
    #
    def run(self, edit, path):
        # Get the contents of the file at the given path
        with open(self.normalize_to_system_style_path(path), "r") as f:
            content = f.read()

        # Get the methods from the content
        self.methods = self.get_methods(content)

        # Show the available methods in the quick panel
        if (len(self.methods) > 1):
            methods = list(map(lambda x: x["method"], self.methods))
            self.view.window().show_quick_panel(methods, self.on_selected)

    # Handles selection of a quick panel item
    #
    def on_selected(self, index):
        if index == -1:
            return

        # Find the closing brackets. We'll place the method
        # stubs just before the last closing bracket.
        closing_brackets = self.view.find_all("[}]")

        # Add the method stub(s) to the current file
        region = closing_brackets[-1]
        point = region.end() - 1

        methods = self.methods[index] if index > 0 else self.methods[1:]
        content = get_setting("stub_content")
        stub = self.generate_stub(methods, content)

        self.view.run_command("create", {"stub": stub, "offset": point})

        # Selects content
        point += stub.find(content) + METHOD_TEMPLATE.find("{1}")

        # Unknown but essential
        docblock_inherit = get_setting("docblock_inherit")
        if docblock_inherit == True:
            point += 3
        elif docblock_inherit == "inheritdoc":
            point += 9

        selection = self.view.sel()
        selection.clear()
        selection.add(sublime.Region(point, point + len(content)))

        # Scroll to selection
        self.view.run_command("show_at_center")

    # Generates stub from template
    #
    def generate_stub(self, methods, content):
        if not isinstance(methods, list):
            methods = [methods]

        stub = ""
        docblock_inherit = get_setting("docblock_inherit")

        for method in methods:
            docblock = method.get("docblock")
            method = method.get("method")

            if docblock != None:
                if docblock_inherit == True:
                    method = docblock + "\n\t" + method
                elif docblock_inherit == "inheritdoc":
                    method = "\n\t".join(["/**", " * {@inheritdoc}", "*/"]) + "\n\t" + method

            stub += METHOD_TEMPLATE.format(method, content)

        return stub
