# Update Matrix
docker-compose -f /root/matrix/docker-compose.yml pull
docker-compose -f /root/matrix/docker-compose.yml up -d

. /usr/share/linux-arbeitsplatz/unix/unix_scripts/env.sh
. /usr/share/linux-arbeitsplatz/unix/unix_scripts/matrix/update_element_config.sh
