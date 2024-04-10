# Needs the environment variable DOMAIN e.g.: int.de

# Write new element config
# Change element app/config.json inside the docker container
echo "Updating element config..."
docker cp element:/app/config.json /root/matrix/config.json
sed -i "s#https://matrix-client.matrix.org#https://matrix.$DOMAIN#g" /root/matrix/config.json
sed -i "s#https://matrix.org#https://matrix.$DOMAIN#g" /root/matrix/config.json
sed -i "s#matrix.org#matrix.$DOMAIN#g" /root/matrix/config.json
sed -i "s#meet.element.io#meet.$DOMAIN#g" /root/matrix/config.json

# Copy the changed config.json back to the docker container
docker cp /root/matrix/config.json element:/app/config.json
rm /root/matrix/config.json

# Restart the element container
docker restart element