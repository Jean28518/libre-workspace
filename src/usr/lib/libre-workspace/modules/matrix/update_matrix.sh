# Update Matrix
docker-compose -f /root/matrix/docker-compose.yml pull
# Matrix Setup sometimes has problems with the network, so we need to remove the containers and start them again
docker-compose -f /root/matrix/docker-compose.yml down
docker-compose -f /root/matrix/docker-compose.yml up -d

# docker compose compatibility:
docker compose -f /root/matrix/docker-compose.yml pull
# Because sometimes docker has problems by itself, we need to remove the containers and start them again
docker compose -f /root/matrix/docker-compose.yml down
docker compose -f /root/matrix/docker-compose.yml up -d

. /etc/libre-workspace/libre-workspace.env
. /usr/lib/libre-workspace/modules/matrix/update_element_config.sh
