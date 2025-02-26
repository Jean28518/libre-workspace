# Needs the environment variable DOMAIN e.g.: int.de

# Write new element config
# Change element app/config.json inside the docker container
echo "Updating element config..."
docker cp element:/app/config.json /root/matrix/
sed -i "s#https://matrix-client.matrix.org#https://matrix.$DOMAIN#g" /root/matrix/config.json
sed -i "s#https://matrix.org#https://matrix.$DOMAIN#g" /root/matrix/config.json
sed -i "s#matrix.org#matrix.$DOMAIN#g" /root/matrix/config.json
sed -i "s#meet.element.io#meet.$DOMAIN#g" /root/matrix/config.json

# Copy the changed config.json back to the docker container
docker cp /root/matrix/config.json element:/app/
rm /root/matrix/config.json

# Fixing bug: https://github.com/element-hq/element-web/issues/29371
docker cp element:/docker-entrypoint.d/18-load-element-modules.sh /tmp/
# Replace the line mkdir /tmp/element-web-config  with mkdir -p /tmp/element-web-config
sed -i "s#mkdir /tmp/element-web-config#mkdir -p /tmp/element-web-config#g" /tmp/18-load-element-modules.sh
docker cp /tmp/18-load-element-modules.sh element:/docker-entrypoint.d/
rm /tmp/18-load-element-modules.sh

# Restart the element container
docker restart element
