@echo off
1>>"%PREFIX%\.messages.txt" 2>&1 (
  "%PREFIX%\Scripts\jupyter-nbextension.exe" enable --sys-prefix --py nbgrader
)
