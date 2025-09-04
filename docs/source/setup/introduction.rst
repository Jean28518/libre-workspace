*******************************
Introduction to Libre Workspace
*******************************

Libre Workspace consists of a set of software packages which should implement a modern cloud infrastructure for companies or individuals. It is based on the following software:

* `Debian <https://www.debian.org/>`_ as the operating system
* `Samba DC <https://wiki.samba.org/index.php/Setting_up_Samba_as_an_Active_Directory_Domain_Controller>`_ as the domain controller and Active Directory implementation
* `Libre Workspace Portal <https://github.com/Jean28518/libre-workspace/>`_ as the central management software for the Libre Workspace based on `Django <https://www.djangoproject.com/>`_ and `gunicorn <https://gunicorn.org/>`_
* `Nextcloud <https://nextcloud.com/>`_ as the cloud storage solution with integrated groupware
* `Collabora Online <https://www.collaboraoffice.com/collabora-online/>`_ or `OnlyOffice <https://www.onlyoffice.com/>`_ as the online office solution (selectable in the Libre Workspace Portal)
* `Jitsi Meet <https://jitsi.org/>`_ as the video conferencing solution
* `Matrix <https://matrix.org/>`_ as the chat solution (with `element <https://element.io/>`_ as the web client)
* `BorgBackup <https://www.borgbackup.org/>`_ as the backup solution
* `Cinnamon <https://linuxmint.com/>`_, `xrdp <https://www.xrdp.org/>`_ and `guacamole <https://guacamole.apache.org/>`_ as the Linux Cloud Desktop solution for the webbrowser.
* `Wordpress <https://wordpress.org/>`_ for creating websites.

Features
========

Next to the softoware components above Libre Workspace provides the following features:

* **Central management** of users, groups (and computers in the future) via the Libre Workspace Portal
* **Single Sign-On** via OpenID Connect (OIDC)
* **2 Factor Authentication** via TOTP (Time-based One-time Password Algorithm) for the Libre Workspace Portal and Nextcloud
* **Backups of the whole system** via BorgBackup - With restore function in the webinterface
* **Automated Updates** via the Libre Workspace Portal
* **Simple installation and configuration** via the Libre Workspace Portal
* **Modular design** - You can install only the components you need
* **REST-API** for easy integration with other software
* **Data import and export** via the Libre Workspace Portal
* **Addon-Support** inclusive an addon store for easy installation of additional modules. Also Addons can be created easily with the integrated addon creator.
* **Adjustable dashboard** for easy application access
* **Web-Server Configuration** inside the Web-Interface for adding additional web applications
* **Theming support** for the Libre Workspace Portal
* **Linux-Client integration** for easy user login on Linux-Clients
* **Multiple language support** - Currently German and English

You can setup the Libre Workspace on your own by following the instructions in this documentation via our automated installation.