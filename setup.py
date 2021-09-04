import sys
from cx_Freeze import setup, Executable
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'
    executables = [
         Executable("hamcrop.py", base=base)]
             
setup(name="hamcrop.exe",
      version='1',
      description='desc',
      executables=executables
      )