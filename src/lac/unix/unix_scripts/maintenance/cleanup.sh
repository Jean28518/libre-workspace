apt clean
apt autoremove -y

docker image prune -a -f
docker volume prune -f