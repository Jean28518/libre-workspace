#################################
New folder structure for Libre Workspace
#################################

- New package name: ``libre-workspace-portal``
- Every addon is a seperate deb package

- File Structure:

  - ``usr``

    - ``lib``

      - ``libre-workspace/portal``

        - (Django project)
        - Folder: ``addons`` (inside are symlinks to the addon folders inside ``/usr/lib/libre-workspace/modules/<addon_name>``)

    - ``bin``

      - ``libre-workspace-portal`` (bash script to run the django project, .env is in ``/var/lib/libre-workspace/portal/venv``)
      - ``libre-workspace-service`` (bash script to run the service.py``)
      - ``libre-workspace-generate-secret`` (with argument ``[length]``), it echoes a random string of the given length
      - ``libre-workspace-remove-webserver-entry`` (with argument of the subdomain)
      - ``libre-workspace-register-oidc-client`` (with arguments of name, client_id, client_secret, redirect_uri(s) (separated by commas))
      - ``libre-workspace-remove-oidc-client`` (with argument of the name)
      - ``libre-workspace-send-mail``
      - ``libre-workspace-set-local-admin-password`` (with argument of the password)
      - ``libre-workspace-reset-2fa`` (with argument of the username)

  - ``etc``

    - ``libre-workspace``

      - ``portal``
        
        - ``portal.conf`` (new file for cfg)

      - ``libre-workspace.conf`` (new file for unix.conf)
      - ``libre-workspace.env`` (new file for env.sh)
      - ``modules``
      
        - (later for module configuration, not yet used)

  - ``var``

    - ``lib``

      - ``libre-workspace/portal``

        - history folder
        - control files of ``libre-workspace-portal``
        - media folder
        - app dashboard settings
        - python venv
