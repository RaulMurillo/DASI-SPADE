import os
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'relative/path/to/file/you/want')

print(os.getcwd())
print(__file__)
print(dirname)
print(filename)
