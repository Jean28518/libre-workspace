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