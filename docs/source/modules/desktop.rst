*******
Desktop
*******

Libre Workspace comes with an linux desktop in your webbrowser.
It is based on Debian Cinnamon and provides a full desktop experience via RDP. As web RDP client guacamole is used which translates the RDP protocol to HTML5 and send then the result to your browser.
As browser chromium or chrome is recommended, but other browsers like firefox or edge should also work but with some limitations, e.g. the clipboard might not work.

Usage
-----

Just open the URL `desktop.int.de` in your browser and log in with your username and password, if asked. OpenID Connect (SSO) is enabled by default.
Users are not able to change any settings of their connection. Administrators instead can set their desktop password inside the libre workspace portal to run e.g. sudo commands at the terminal inside the desktop.
But please be aware that the all other services like nextcloud, matrix, etc. are running on the same machine. So please be careful with what you do inside the desktop, as it might affect the other services.
Users are not able to change anything at the system level, so they cannot install new software or change the system configuration. The desktop is meant to be a user-friendly environment for daily tasks like document editing, web browsing, and communication.

Keyboard Layout and other Settings
==================================

The default desktop keyboard layout is set to "German" (de). 
If you want to change the keyboard layout, an administrator can edit the corresponding connection inside the guacamole configuration.
You can reach them by opening desktop.int.de and then pressing the shortcut "Ctrl + Shift + Alt" to open the guacamole settings. Then click on your username, select "Settings" and then "Connections".
You can then edit the connection and change the keyboard layout to your desired one. Dont forget to hit "Save" at the bottom after changing the settings.