**********************
Linux Client User Sync
**********************

The Libre Workspace Project provides a script to sync users and libre workspace groups from the Libre Workspace Portal to the Linux client.
These properties are synced:

- Username
- Display name
- Password
- Activation status
- User id (uid) (starting at 10000)
- Administrator status
- Groups

At the moment there is no two factor authentication support for login at a client. So a user will only need his normal libre workspace password to log in.

.. note:: If the Administrator is not able to login at the client, make sure to login once via the web portal first once. Then try syncing the users again. The "Administrator" user is the only user with a uppercase letter and always has the uid 10000.

Setup Example
-------------
To set up the user sync script, you can create a cron job that runs the script at regular intervals.
For example, to run the script every hour. Here is a full example how to set up your linux client:

- Login via administrator in to the Libre Workspace Portal.
- Create an API key with the permission "Linux Client" and copy the key.

code-block:: bash

    # If your libre workspace instance is available via int.de we have to install the CA certificate:
    sudo wget --no-check-certificate https://cert.int.de/lan.crt -O /usr/local/share/ca-certificates/cert.int.de.crt
    sudo update-ca-certificates

    sudo apt install wget
    sudo mkdir -p /root/scripts
    sudo wget https://raw.githubusercontent.com/linux-arbeitsplatz/linux-arbeitsplatz-central/main/src/join_scripts/linux-client/sync_linux_users.py -O /root/scripts/sync_linux_users.py
    sudo chmod +x /root/scripts/sync_linux_users.py
    sudo nano /root/scripts/sync_linux_users.py
    # Update the environment variables LIBRE_WORKSPACE_URL and API_KEY at the top of the file
    

    # Try now to run the script manually and check if it works:
    sudo /root/scripts/sync_linux_users.py
    
    # If it works you can set up a cron job to run the script every hour:
    sudo crontab -e
    5 * * * * /root/scripts/sync_linux_users.py >> /var/log/sync_linux_users.log 2>&1


Perfect! You may use the same API key for multiple clients.