apt clean
apt autoremove -y

docker image prune -a -f
docker volume prune -f

sudo journalctl --vacuum-size=1G

# To address the possible memory leak described in https://github.com/Jean28518/libre-workspace/issues/92
systemctl restart linux-arbeitsplatz-web.service