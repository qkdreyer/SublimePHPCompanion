import sublime
import sublime_plugin

import os
import re

from ..settings import get_setting


class ImportNamespaceCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # Filename to namespace
        file_name = self.view.file_name()

        # Abort if the file is not PHP
        if not file_name.endswith('.php'):
            sublime.error_message('No .php extension')
            return

        # Ignores lowercased file names
        if os.path.basename(file_name)[0].isupper():
            # namespace begin at first camelcase dir
            namespace_stmt = os.path.dirname(file_name)
            pattern = re.compile(get_setting(
                'start_dir_pattern', '^.*?((?:\/[A-Z][^\/]*)+)$'))
            namespace_stmt = re.sub(pattern, '\\1', namespace_stmt)
            namespace_stmt = re.sub('/', '\\\\', namespace_stmt)
            namespace_stmt = namespace_stmt.strip('\\')

        # Add an optional prefix - may be per project
        namespace_prefix = get_setting('namespace_prefix', '').strip('\\')
        if namespace_prefix:
            if namespace_stmt:
                namespace_prefix += '\\'
            namespace_stmt = namespace_prefix + namespace_stmt

        # Ensuring PHP tag presence
        php_tag = '<?php'
        php_regex = php_tag.replace('?', '\?')
        php_region = self.view.find(php_regex, 0)
        if php_region.empty():
            line = self.view.line(php_region)
            self.view.insert(edit, 0, php_tag)

        # Removing existing namespace
        namespace_region = self.view.find(r'\s*namespace\s[\w\\]+;', 0)
        if not namespace_region.empty():
            self.view.replace(edit, namespace_region, '')

        # Adding namespace
        if namespace_stmt:
            inline_namespace = get_setting('namespace_position') == 'inline'
            namespace_contents = ' ' if inline_namespace else '\n\n'
            namespace_contents += 'namespace ' + namespace_stmt + ';'
            if not inline_namespace:
                php_regex += r'(\s*\/\*(?:[^*]|\n|(?:\*(?:[^\/]|\n)))*\*\/)?'
            php_docblock_region = self.view.find(php_regex, 0)
            if not php_docblock_region.empty():
                line = self.view.line(php_docblock_region)
                self.view.insert(edit, line.end(), namespace_contents)
