# Linux-Arbeitsplatz Zentrale

Using Samba as domain controller.

## How to deploy

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
central.int.de {
  handle_path /static* {
        root * /var/www/linux-arbeitsplatz-static
        file_server
        encode zstd gzip
  }
  reverse_proxy localhost:11123
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
