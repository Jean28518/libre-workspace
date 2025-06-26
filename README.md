# Libre Workspace

### [Website](https://www.libre-workspace.org/)
### [Documentation](https://docs.libre-workspace.org/)
### [Download](https://github.com/Jean28518/libre-workspace/releases/latest)

![Libre Workspace](https://www.libre-workspace.org/wp-content/uploads/2024/01/Design-ohne-Titel.jpg)

- **Your data stays with you**
- **Cloud for files, calendars, Office, chats, conferences ...**
- **Open source by definition**

## Technical Information

Libre Workspace consists of a set of software packages which should implement a modern cloud infrastructure for small companies or individuals. It is based on the following software:

- Debian as the operating system
- Samba DC as the domain controller and Active Directory implementation
- Libre Workspace Portal as the central management software for the Libre Workspace
- Nextcloud as the cloud storage solution with integrated groupware
- Jitsi Meet as the video conferencing solution
- Matrix as the chat solution (with element as the web client)
- BorgBackup as the backup solution
- Extendable with [addons](https://docs.libre-workspace.org/modules/addons.html)

## How to install

<https://docs.libre-workspace.org/setup/installation.html>

(Otherwise you can see the installation in /docs/setup/installation.rst)

### 🎞️ Video Tutorial Series (in German) 🎞️

<https://www.youtube.com/watch?v=tzs9SdfeOMc&list=PL26JW41WknwissQLa5JSEnGui9rHppYXB>

## Technical Information for Developers

Make sure to check the documentation in /docs or at <https://docs.libre-workspace.org/>

### Build .iso

```bash
sudo apt install syslinux-utils git
git clone https://github.com/Jean28518/libre-workspace
cd libre-workspace
bash download_debian_iso.sh
bash build_deb.sh
sudo bash build_iso.sh
```

You can access the installer at port 80 and 443. (After installing the debian base system).
Your default account is called "Administrator".

## How to develop

```bash
# Make sure on your dev machine no actual libre workspace component is installed.
# Start from this directory
sudo apt-get install libldap2-dev python3-venv libsasl2-dev python3-dev
sudo mkdir -p /var/www/libre-workspace-static
sudo chown -R $USER:$USER /var/www/libre-workspace-static
sudo ln -s $PWD/src/etc/libre-workspace/ /etc/libre-workspace
sudo ln -s $PWD/src/usr/lib/libre-workspace /usr/lib/libre-workspace
sudo ln -s $PWD/src/var/lib/libre-workspace/ /var/lib/libre-workspace

cd /var/lib/libre-workspace/portal
python3 -m venv venv
cd -
cp /etc/libre-workspace/portal/portal.conf.example /etc/libre-workspace/portal/portal.conf
vim /etc/libre-workspace/portal/portal.conf # Configure
cp /etc/libre-workspace/libre-workspace.env.example /etc/libre-workspace/libre-workspace.env


# If you did the setup above once, you can start the django server with this command
bash run_development.sh
# Start unix service (in a second terminal session)
cd src/
bash usr/bin/libre-workspace-service


# To clean later your computer after ending the development:
sudo rm -rf /var/www/libre-workspace-static
sudo rm /etc/libre-workspace
sudo rm /usr/lib/libre-workspace
sudo rm /var/lib/libre-workspace
```

## Build documentation

The documentation is also accessible at <https://docs.libre-workspace.org/>

```bash
sudo apt install python3-sphinx python3-sphinx-rtd-theme
bash build_docs.sh
```

You find the generated html files in docs/_build
