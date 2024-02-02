cd /root/matrix

# Update Matrix
docker-compose pull
docker-compose up -d

cd /usr/share/linux-arbeitsplatz/unix/unix_scripts/
. env.sh
. update_element_config.sh