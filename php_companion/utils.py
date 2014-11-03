import sublime

import re
import mmap
import contextlib
import subprocess
import json

from .settings import get_setting

def normalize_to_system_style_path(path):
    if sublime.platform() == "windows":
        path = re.sub(r"/([A-Za-z])/(.+)", r"\1:/\2", path)
        path = re.sub(r"/", r"\\", path)
    return path

def find_symbol(symbol, window):
    files = window.lookup_symbol_in_index(symbol)
    namespaces = []
    pattern = re.compile(b'namespace\s+([^;]+);', re.MULTILINE)

    def filter_file(file):
        if get_setting('exclude_dir', False):
            for pattern in get_setting('exclude_dir', False):
                pattern = re.compile(pattern)
                if pattern.match(file[1]):
                    return False

        return file

    for file in files:
        if filter_file(file):
            with open(normalize_to_system_style_path(file[0]), "rb") as f:
                with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
                    for match in re.findall(pattern, m):
                        namespace = match.decode('utf-8') + "\\" + symbol
                        namespaces.append([namespace, file[1]])
                        break

    if get_setting('allow_use_from_global_namespace', False):
        namespaces += find_in_global_namespace(symbol)

    data = get_priorities(window)

    namespaces = sorted(namespaces, key=lambda namespace: str(data.get(namespace[0], 0)), reverse=True)

    return namespaces

def find_in_global_namespace(symbol):
    definedClasses = subprocess.check_output(["php", "-r", "echo json_encode(get_declared_classes());"]);
    definedClasses = definedClasses.decode('utf-8')
    definedClasses = json.loads(definedClasses)
    definedClasses.sort()

    matches = []
    for phpClass in definedClasses:
        if symbol == phpClass:
            matches.append([phpClass, phpClass, 0])

    return matches

def increment_namespace_use(window, namespace):
    priorities = get_priorities(window)
    priorities[namespace] = priorities.get(namespace, 0) + 1
    data = window.project_data()
    data['priorities'] = priorities
    window.set_project_data(data)

def get_priorities(window):
    projectData = window.project_data()
    return projectData.get('priorities', {})
