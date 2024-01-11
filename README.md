# Linux-Arbeitsplatz Zentrale

Using Samba as domain controller.

## Build .iso

```bash
sudo apt install syslinux-utils git
git clone https://github.com/Jean28518/linux-arbeitsplatz-central.git
cd linux-arbeitsplatz-central
bash download_debian_iso.sh
bash build_deb.sh
sudo bash build_iso.sh
```

You can access the installer at port 80 and 443. (After installing the debian base system).
Your default account is called "Administrator".

## How to deploy (only Linux-Arbeitpsplatz Zentrale)

```bash
# Make sure you have AD domain controler like samba active and ldaps enabled.

wget https://github.com/Jean28518/linux-arbeitsplatz-central/releases/download/v0.1.0/linux-arbeitsplatz.deb
sudo apt install ./linux-arbeitsplatz.deb

vim /usr/share/linux-arbeitsplatz/cfg
# Adjust all variables

systemctl enable linux-arbeitsplatz-web --now
systemctl enable linux-arbeitsplatz-unix --now
systemctl restart linux-arbeitsplatz-web
```

### Caddyfile

```Caddyfile
portal.int.de {
  handle_path /static* {
        root * /var/www/linux-arbeitsplatz-static
        file_server
        encode zstd gzip
  }
  reverse_proxy localhost:11123
}

# Access description for new libre workspace users
[IP] {
    #tls internal
    handle_path /static* {
        root * /var/www/linux-arbeitsplatz-static
        file_server
        encode zstd gzip
    } 
    handle {
    rewrite * /welcome/access
    reverse_proxy localhost:11123
    }
}
```

## How to develop

```bash
sudo apt-get install libldap2-dev python3-venv libsasl2-dev python3-dev
cd src/lac/
python3 -m venv .env
cd ../../
cp cfg.example cfg
vim cfg # Configure example


# If you did the setup above once, you can start the django server with this command
bash run_development.sh
# Start unix service (in a second terminal session)
bash unix_service.sh
```

## Build documentation

```bash
sudo apt install python3-sphinx python3-sphinx-press-theme
bash build_docs.sh
```

You find the generated html files in docs/_build

