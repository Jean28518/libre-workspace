mkdir -p deb/usr/share/linux-arbeitsplatz
cp -r src/lac/* deb/usr/share/linux-arbeitsplatz/

# Disable DEBUG mode
sed -i "s/DEBUG = True/DEBUG = False/g" deb/usr/share/linux-arbeitsplatz/lac/settings.py

cp install.sh deb/usr/share/linux-arbeitsplatz
cp run.sh deb/usr/share/linux-arbeitsplatz
cp unix_service.sh deb/usr/share/linux-arbeitsplatz
cp cfg.example deb/usr/share/linux-arbeitsplatz/
cp openbox-autostart deb/usr/share/linux-arbeitsplatz/
cp prepare_for_first_boot.sh deb/usr/share/linux-arbeitsplatz/

chmod +x deb/usr/share/linux-arbeitsplatz/install.sh
chmod +x deb/usr/share/linux-arbeitsplatz/run.sh
chmod +x deb/usr/share/linux-arbeitsplatz/unix_service.sh

chmod 755 deb/DEBIAN
chmod 755 deb/DEBIAN/postinst

dpkg-deb --build -Zxz deb 
mv deb.deb linux-arbeitsplatz.deb

echo "!!!Ensure that you build the deb package from a fresh cloned repository! (Otherwise some control files might disturb linux-arbeitplatz later)!!!"