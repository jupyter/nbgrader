version_info = (0, 8, 0, "dev")
__version__ = '.'.join(map(str, version_info[:3])) + (("." + version_info[3]) if version_info[3] else "")
