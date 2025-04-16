mkdir -p deb/usr/share/linux-arbeitsplatz
cp -r src/lac/* deb/usr/share/linux-arbeitsplatz/

# Disable DEBUG mode
sed -i "s/DEBUG = True/DEBUG = False/g" deb/usr/share/linux-arbeitsplatz/lac/settings.py
# Disable Admin site (ADMIN_ENABLED)
sed -i "s/ADMIN_ENABLED = True/ADMIN_ENABLED = False/g" deb/usr/share/linux-arbeitsplatz/lac/settings.py

cp install.sh deb/usr/share/linux-arbeitsplatz
cp run.sh deb/usr/share/linux-arbeitsplatz
cp unix_service.sh deb/usr/share/linux-arbeitsplatz
cp cfg.example deb/usr/share/linux-arbeitsplatz/
cp openbox-autostart deb/usr/share/linux-arbeitsplatz/
cp prepare_for_first_boot.sh deb/usr/share/linux-arbeitsplatz/
cp requirements.txt deb/usr/share/linux-arbeitsplatz/
cp update_libre_workspace.sh deb/usr/share/linux-arbeitsplatz/
cp django_reset_2fa_for_Administrator.sh deb/usr/share/linux-arbeitsplatz/
cp django_set_local_Administrator_password.sh deb/usr/share/linux-arbeitsplatz/
cp django_add_oidc_provider_client.sh deb/usr/share/linux-arbeitsplatz/

chmod +x deb/usr/share/linux-arbeitsplatz/install.sh
chmod +x deb/usr/share/linux-arbeitsplatz/run.sh
chmod +x deb/usr/share/linux-arbeitsplatz/unix_service.sh

chmod 755 deb/DEBIAN
chmod 755 deb/DEBIAN/postinst

dpkg-deb --build -Zxz --root-owner-group deb 
mv deb.deb linux-arbeitsplatz.deb

echo "!!!Ensure that you build the deb package from a fresh cloned repository! (Otherwise some control files might disturb linux-arbeitplatz later)!!!"