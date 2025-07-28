# Copy the files to the debian package structure
if [ -d build/deb ]; then
    rm -rf build/deb
fi
mkdir -p build/
cp -r deb/ build/deb

cp -r src/usr build/deb/
cp -r src/etc build/deb/

# Disable Admin site (ADMIN_ENABLED)
sed -i "s/ADMIN_ENABLED = True/ADMIN_ENABLED = False/g" build/deb//usr/lib/libre-workspace/portal/lac/settings.py

# Remove all .gitignore and .gitkeep files
find build/deb/ -name ".gitignore" -type f -delete
find build/deb/ -name ".gitkeep" -type f -delete

chmod +x build/deb/usr/lib/libre-workspace/portal/install.sh
chmod +x build/deb/usr/bin/*

chmod 755 build/deb/DEBIAN
chmod 755 build/deb/DEBIAN/postinst

cd build/
dpkg-deb --build -Zxz --root-owner-group deb 
mv deb.deb libre-workspace-portal.deb

echo "!!!Ensure that you build the deb package from a fresh cloned repository! (Otherwise some control files might disturb linux-arbeitplatz later)!!!"