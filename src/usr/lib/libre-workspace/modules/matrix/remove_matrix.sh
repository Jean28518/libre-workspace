# Removes also all data!
# Needs the following variables:
# DOMAIN

python3 ../remove_caddy_service.py element.$DOMAIN
python3 ../remove_caddy_service.py matrix.$DOMAIN

cd /root/matrix
docker-compose down --volumes
cd -

rm -r /root/matrix
