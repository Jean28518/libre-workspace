cd /root/matrix

# Update Matrix
docker-compose pull
docker-compose up -d

. ../env.sh
. update_element_config.sh