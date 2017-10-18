import sublime_plugin
import re

from ..settings import get_setting

class FixImportsListener(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        self.view = view
        self.window = view.window()

        enable_fix_imports_on_save = get_setting('enable_fix_imports_on_save', False)
        file_name = view.file_name()

        if isinstance(enable_fix_imports_on_save, str):
            search = re.search(enable_fix_imports_on_save, file_name)
            enable_fix_imports_on_save = search != None

        if enable_fix_imports_on_save:
            view.run_command('fix_imports')
