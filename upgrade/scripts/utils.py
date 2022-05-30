from sys import platform


def is_windows():
    return platform == "win32" or platform == "cygwin"
