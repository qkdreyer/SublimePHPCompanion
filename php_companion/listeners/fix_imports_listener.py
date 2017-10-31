import sublime_plugin
import re
import os

from ..settings import get_setting

class FixImportsListener(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        self.view = view
        self.window = view.window()

        enable_fix_imports_on_save = get_setting('enable_fix_imports_on_save', False)
        file_name = view.file_name()

        if file_name.find(os.environ.get('TMPDIR')) == 0:
            enable_fix_imports_on_save = False
        elif isinstance(enable_fix_imports_on_save, str):
            enable_fix_imports_on_save = re.search(enable_fix_imports_on_save, file_name) != None

        if enable_fix_imports_on_save is True:
            view.run_command('fix_imports')
