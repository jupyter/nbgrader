import os

def get_template_path():
    f = __file__
    return os.path.abspath(os.sep.join(f.split(os.sep)[:-1]))

def get_template(name):
    path = get_template_path()
    filename = os.path.join(path,name+'.tpl')
    if not os.path.isfile(filename):
        raise IOError("Template file doesn't exist: %s" % filename)
    return filename
