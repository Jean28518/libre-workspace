# Update Matrix
docker-compose -f /root/matrix/docker-compose.yml pull
docker-compose -f /root/matrix/docker-compose.yml up -d

. ../env.sh
. update_element_config.sh
