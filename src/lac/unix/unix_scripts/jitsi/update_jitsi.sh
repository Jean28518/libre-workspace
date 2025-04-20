cd /root/jitsi

# Ensure that in the .env file the variable "JITSI_IMAGE_VERSION" is set to "stable"
# Delete the line with "JITSI_IMAGE_VERSION=latest"
sed -i "/JITSI_IMAGE_VERSION/d" .env
# Add the line "JITSI_IMAGE_VERSION=stable"
echo "JITSI_IMAGE_VERSION=stable" >> .env

# Update Jitsi
docker-compose down # To avoid problems with the containers after the update
docker-compose pull
docker-compose up -d


# docker compose compatibility:
docker compose pull
# Because sometimes docker has problems by itself, we need to remove the containers and start them again
docker compose down
docker compose up -d