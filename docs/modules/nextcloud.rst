*********
Nextcloud
*********

Nextcloud is one of the main modules of libre workspace.
It is deployed directly on the server with php, mariadb, and caddy as a webserver.

Also all recommended php options are enabled and all recommended php modules are installed.
The automated installer of libre workspace doesn't setup a memory cache for php. 
If you want to setup a memory cache redis is recommended.

Nextcloud is installed in the directory ``/var/www/nextcloud``.

Online Office
=============

As online office libre workspace uses whether Collabora Online or OnlyOffice.
These are deployed via simple docker files and docker-compose. 
The configuration for that is in ``/root/``.

How to update
=============

You can easily update nextcloud via the web interface or enabling the automatic updates for it in the libre workspace portal.
Please have in mind that on old servers (or php versions) nextcloud will not work anymore after an update because of the php version. 
In this case you have to update php first and/or the server itself.

The docker tag of Collabora Online and OnlyOffice is ``latest``. 
You can also enable automatic updates for the docker containers in the libre workspace portal, which is highly recommended.
Otherwise you can easily remove the corresponding docker container and start the deployment process via the run.sh files in ``/root/`` again.

Can I also integrate an existing Nextcloud to libre workspace?
==============================================================

Yes, of course this is possible! If your nextcloud is installed in the directory ``/var/www/nextcloud`` then nothing has to be done, that libre workspace can work with it. Otherwise an ``ln -s`` is recommended. 
If the nextcloud instance is installed at another server you can also integrate it to libre workspace. e.g. with an caddy redirect or add a specific link at the libre workspace portal.

It is not recommended to connect the user database of libre workspace with an existing nextcloud via e.g. ldap, or SSO because ldap and SSO are using an objectid for the nextcloud username (internally) so your existing users would be "changed" to new users. (Your data will not be lost, but the user will be "linked" to a new one.)

You can also move (if you want) your existing nextcloud webserver to caddy, which is recommended for libre workspace. You can find the complete nextcloud caddy entry here: https://github.com/Jean28518/libre-workspace/blob/main/src/lac/unix/unix_scripts/nextcloud/caddy_nextcloud_entry.txt (You have to replace "SED_DOMAIN" with your real domain name.)
