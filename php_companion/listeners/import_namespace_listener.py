import sublime
import sublime_plugin
import re

class ImportNamespaceListener(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        settings = sublime.load_settings('PHP Companion.sublime-settings')
        enable_import_namespace_on_save = settings.get('enable_import_namespace_on_save', False)
        file_name = view.file_name()

        if isinstance(enable_import_namespace_on_save, str):
            search = re.search(enable_import_namespace_on_save, file_name)
            enable_import_namespace_on_save = search != None

        if enable_import_namespace_on_save and file_name.endswith('.php'):
            view.run_command('import_namespace')
