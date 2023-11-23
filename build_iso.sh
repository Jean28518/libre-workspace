arch="amd"

# Prepare working files for manipulating iso file
mkdir ORIGISO
mkdir NEWISO
mount -o loop debian-original.iso ./ORIGISO
cp -rT ./ORIGISO/ ./NEWISO/
umount ./ORIGISO 

# Write preseed.cfg into new iso
chmod +w -R ./NEWISO/install.$arch/
gunzip ./NEWISO/install.$arch/gtk/initrd.gz
echo preseed.cfg | cpio -H newc -o -A -F ./NEWISO/install.$arch/gtk/initrd
gzip ./NEWISO/install.$arch/gtk/initrd
chmod -w -R ./NEWISO/install.$arch

# Copy the custom package (which does the installation of linux-arbeitsplatz in the end) to the new iso
cp linux-arbeitsplatz.deb ./NEWISO/

# Generate new md5sums
chmod +w ./NEWISO/md5sum.txt
cd NEWISO
find -follow -type f ! -name md5sum.txt -print0 | xargs -0 md5sum > ./md5sum.txt
chmod -w ./md5sum.txt
cd ..

# Generate new iso image
genisoimage -r -J -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot -o linux-arbeitsplatz.iso ./NEWISO
isohybrid --uefi linux-arbeitsplatz.iso
rm -rf ./ORIGISO ./NEWISO