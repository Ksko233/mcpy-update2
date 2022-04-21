@echo off
title setup.bat

:INFO
echo This command-line setup will guide you to install Minecraft Python Edition.
echo Press any key ...
pause>nul

:INSTALL
cls
echo Wait for pip...
pip3 install pyglet
cls
echo Wait for pip...
pip3 install --upgrade pyglet
cls
echo Wait for pip...
pip3 install easygui
cls
echo Wait for pip...
pip3 install --upgrade easygui
cls

:FINISH
echo You have installed Minecraft Python Edition.
echo Press any key to exit ...
pause>nul
exit