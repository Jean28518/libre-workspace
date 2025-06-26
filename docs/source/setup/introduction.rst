*******************************
Introduction to Libre Workspace
*******************************

Libre Workspace consists of a set of software packages which should implement a modern cloud infrastructure for small companies or individuals. It is based on the following software:

* `Debian <https://www.debian.org/>`_ as the operating system
* `Samba DC <https://wiki.samba.org/index.php/Setting_up_Samba_as_an_Active_Directory_Domain_Controller>`_ as the domain controller and Active Directory implementation
* `Libre Workspace Portal <https://github.com/Jean28518/libre-workspace/>`_ as the central management software for the Libre Workspace
* `Nextcloud <https://nextcloud.com/>`_ as the cloud storage solution with integrated groupware
* `Jitsi Meet <https://jitsi.org/>`_ as the video conferencing solution
* `Matrix <https://matrix.org/>`_ as the chat solution (with `element <https://element.io/>`_ as the web client)
* `BorgBackup <https://www.borgbackup.org/>`_ as the backup solution

Features
========
The Libre Workspace is a complete solution for small companies or individuals. It provides the following features:

* **Central management** of users, groups (and computers in the future) via the Libre Workspace Portal
* **File storage and sharing** via Nextcloud
* **Groupware (calendar, contacts, tasks, mail)** via Nextcloud
* **Online Office** via Collabora Online or OnlyOffice (selectable in the Libre Workspace Portal)
* **Video conferencing** via Jitsi Meet
* **Chat** via Matrix (with the web client **element**) (Groupchats, Spaces, End-to-End Encryption, File Sharing, small Video Calls, Voice Calls, direct Messages, etc.)
* **Backups of the whole system** via BorgBackup - With restore function via the Libre Workspace Portal
* **Data import and export** via the Libre Workspace Portal
* **Simple installation and configuration** via the Libre Workspace Portal
* **Addon-Support** (e.g. for additional software like ERP, CRM, etc.)
  
Limitations
===========
All limitations are temporary and will be removed in the future.

- At the current time the Libre Workspace is only available in German.
- Currently the Libre Workspace automation is in BETA status. If you want to use it in production, feel free to contact us to get support: https://www.linuxguides.de/
- Currently we don't have an automated solution for mail. At the current time you have to use an external mail provider or setup your own mail server.

You can setup the Libre Workspace on your own by following the instructions in this documentation via our automated installation.