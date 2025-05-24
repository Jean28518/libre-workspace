# Copy the files to the debian package structure
cp -r src/usr deb/
cp -r src/etc deb/
cp -r src/var deb/

# Disable DEBUG mode
sed -i "s/DEBUG = True/DEBUG = False/g" deb/usr/lib/libre-workspace/portal/lac/settings.py
# Disable Admin site (ADMIN_ENABLED)
sed -i "s/ADMIN_ENABLED = True/ADMIN_ENABLED = False/g" deb//usr/lib/libre-workspace/portal/lac/settings.py

chmod +x deb/usr/lib/libre-workspace/portal/install.sh
chmod +x deb/usr/bin/*

chmod 755 deb/DEBIAN
chmod 755 deb/DEBIAN/postinst

dpkg-deb --build -Zxz --root-owner-group deb 
mv deb.deb libre-workspace.deb

echo "!!!Ensure that you build the deb package from a fresh cloned repository! (Otherwise some control files might disturb linux-arbeitplatz later)!!!"