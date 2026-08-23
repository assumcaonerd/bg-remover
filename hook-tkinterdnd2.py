"""PyInstaller hook for tkinterdnd2.

Place this file in the project root and build with:
  pyinstaller --additional-hooks-dir=. ...
"""
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("tkinterdnd2")
