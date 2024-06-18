**********************
General Administration
**********************

SSH-Access
==========

You can access the server via SSH on Port 22 with for example the following commands:

.. code-block:: bash

    ssh systemv@<IP-Address>
    ssh systemv@portal.int.de

The password is the same as the one you use to log in to the web interface. 
If you want to log in before you have set the master password, the password is ``LibreWorkspace``.

You can become root with the following command:

.. code-block:: bash

    sudo -i

The password is the same as the one you use to log in into SSH.


Web Server
==========

Basics
------

The default web server is Caddy. You can find the configuration file ("Caddyfile") at ``/etc/caddy/Caddyfile``.
You can edit it with e.g. ``sudo nano /etc/caddy/Caddyfile``.
You can restart the web server with the following command: ``sudo systemctl restart caddy``.
If a ``#`` is in front of a line, it is a comment and will be ignored by the web server.

If you are working with the Caddyfile for your first time, then maybe this will help you: https://caddyserver.com/docs/caddyfile-tutorial


If your instance is a local one, then ``internal tls`` is used for every entry.
Also Caddy is then the CA (Certificate Authority) for the internal tls, you can find it in ``cert.int.de`` if you want to add it to your trusted CAs.

Can I replace Caddy with another web server?
--------------------------------------------

Generally yes, but you have to ensure that the caddy entries are 'translated' to the new web server.
But because of automatic actions like installation/removal of modules it's highly recommended to stay using caddy.

Can I set Caddy behind a reverse proxy?
----------------------------------------

Caddy still acts in many cases as a reverse proxy. 
So if you really want, then you can remove some entries of the Caddyfile and let the reverse proxy do the rest.

The only applications which 'rely' on caddy as a webserver is the Libre Workspace Portal and nextcloud.
It would be okay if you change the values of these services to serve at another port that port 80/443 are free for the reverse proxy.

Your Caddyfile would change like this:

.. code-block:: yaml

    # Initial would look like this:
    cloud.int.de {
        tls internal 

        handle_path /index.php/settings/users {
        # ...


    # After the change for your reverse proxy the caddy entry would look like this:
    :50000 {
        #tls internal 

        handle_path /index.php/settings/users {
        # ...
    
    # Then your reverse proxy has to forward the requests to the new port 50000.

.. hint:: Don't forget to add the port to the firewall (``ufw allow 50000``) and to restart caddy after you have changed the Caddyfile: ``sudo systemctl restart caddy``


Run behind my router but with internet access?
----------------------------------------------

If you want to run your instance behind a router (in your local network) (NAT) but you still want to access it from the internet,
you regulary have do following steps:

- Check if your internet access has a IPv4 address. IPv6 could be very difficult to handle.
- If you IPv4 address is changing over the time you have to set up a dynamic DNS service on your router.
- You have to forward the ports 80/TCP and 443/TCP to your server on your router. (Also port 10000/UDP if you want to use jitsi) (Port Forwarding)
- At the time it's highly recommended to use a full domain (second level) (like: my-libre-workspace.com) for your instance. The Domain should have CNAME entries for the dynamic DNS service. So if your dynDNS address is e.g. ``myserver.dyndns.org`` then a valid DNS-Entry would be ``Name: * Type: CNAME Value: myserver.dyndns.org``.
- And then you can define in the Libre Workspace Installation the public domain.


Change existing libre workspace from local to public
----------------------------------------------------

There is no automatic way to do this, but you can do it manually.

- Do the steps from the previous section, if you haven't done it yet. (Without the installation in the end ;) )
- The main steps are in the Caddyfile. You have to change every caddy entry like this:

.. code-block:: yaml

    # Before
    cloud.int.de {
        tls internal

    # After
    cloud.my-libre-workspace.com {
        #tls internal

.. note:: Sadly there is no option to change the matrix domain. So if you have a user with the ID ``@user:int.de`` then it will stay like this.

Make also sure for the next automated processes that the domain is set correctly in the Libre Workspace env.sh file:

``sudo nano /usr/share/linux-arbeitsplatz/unix/unix_scripts/env.sh``

``export DOMAIN=my-libre-workspace.com``

.. warning:: Do not change the LDAP_DC variable in the env.sh file. This can't be changed after the installation. But it shouldn't bother you anyway.

Also you need to add the new cloud.my-libre-workspace.com to nextcloud as a trusted domain and set the overwrite.cli.url to the new domain:

.. code-block:: bash

    sudo -u www-data php /var/www/nextcloud/occ config:system:set trusted_domains 2 --value=cloud.my-libre-workspace.com
    sudo -u www-data php /var/www/nextcloud/occ config:system:set overwrite.cli.url --value=https://cloud.my-libre-workspace.com

Also some other additional services like jitsi or collabora need to be adjusted to the new domain. Unless these both services do not store any data, you can just reinstall them in the web interface.

In the end a restart of the whole server is recommended.


Can I only make e.g. nextcloud public?
---------------------------------------

Yes, this is possible! Then all the rest of the services are then only available in your local network, but nextcloud is both available from the internet and your local network. You have to duplicate the Caddyfile entry for cloud.int.de and change the domain to the public one. (Change the domain and remove the tls internal line)
Also make sure that trusted domains and overwrite.cli.url are set correctly in nextcloud, as described in the previous section.


How is it with HTTPS-Certificates?
----------------------------------

The certificates are automatically generated and renewed by Caddy. 
If you want to use your own certificates, you can replace the files in ``/etc/caddy/certs``.
But usually you don't need to bother with this.

The caddy documentation allows much more options than described in this documentation. You will find the documentation at https://caddyserver.com/docs/caddyfile/directives