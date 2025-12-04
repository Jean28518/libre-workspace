arch="amd"

# Remove old iso file if it exists
if [ -f libre-workspace.iso ]; then
    rm -f libre-workspace.iso
fi
# Remove the NEWISO and ORIGISO folders if they exist
if [ -d ORIGISO ]; then
    rm -rf ORIGISO
fi
if [ -d NEWISO ]; then
    rm -rf NEWISO
fi

# Prepare working files for manipulating iso file
mkdir ORIGISO
mkdir NEWISO
mount -o loop debian-original.iso ./ORIGISO
cp -rT ./ORIGISO/ ./NEWISO/
umount ./ORIGISO 

# Write preseed.cfg and graphic into new iso
chmod +w -R ./NEWISO/install.$arch/
gunzip ./NEWISO/install.$arch/gtk/initrd.gz
echo preseed.cfg | cpio -H newc -o -A -F ./NEWISO/install.$arch/gtk/initrd

# Extraxt initrd.gz
cd ./NEWISO/install.$arch/gtk/
mkdir tmp && cd tmp
cpio -i -F ../initrd -d 

# Overwrite libre workspace header with debian header
cd ../../../../
cp libre_workspace_header.png ./NEWISO/install.$arch/gtk/tmp/usr/share/graphics/logo_debian.png
cd ./NEWISO/install.$arch/gtk/tmp

# Repack initrd.gz
rm ../initrd
find . | cpio -o -H newc -F ../initrd
cd ../../../../
rm -rf ./NEWISO/install.$arch/gtk/tmp
gzip ./NEWISO/install.$arch/gtk/initrd
chmod -w -R ./NEWISO/install.$arch

# Copy the custom package (which does the installation of libre-workspace in the end) to the new iso
cp build/libre-workspace-portal.deb ./NEWISO/
cp install-libreworkspace.sh ./NEWISO/install-libreworkspace.sh
chmod +x ./NEWISO/install-libreworkspace.sh
cp first-boot-installation.service ./NEWISO/first-boot-installation.service

# Change the boot menu to automatically start the installation
sed -i "s/timeout 300/timeout 1/g" ./NEWISO/isolinux/spkgtk.cfg
sed -i "s/speakup.synth=soft //g" ./NEWISO/isolinux/spkgtk.cfg

# Change the installer graphic to the one from libre workspace
cp splash.png ./NEWISO/isolinux/splash.png

# Generate new md5sums
chmod +w ./NEWISO/md5sum.txt
cd NEWISO
find -follow -type f ! -name md5sum.txt -print0 | xargs -0 md5sum > ./md5sum.txt
chmod -w ./md5sum.txt
cd ..

# Generate new iso image
xorrisofs -r -J -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot -o libre-workspace.iso ./NEWISO
isohybrid --uefi libre-workspace.iso
rm -rf ./ORIGISO ./NEWISO