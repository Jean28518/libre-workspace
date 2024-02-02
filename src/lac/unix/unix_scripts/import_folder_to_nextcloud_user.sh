touch nextcloud_import_process_running

# Get date in format: yyyy-mm-dd-hh-mm-ss
DATE=$(date +"%Y%m%d%H%M%S")

mkdir -p $NEXTCLOUD_USER_FOLDER/Import-$DATE/
cp -r $FOLDER_IMPORT $NEXTCLOUD_USER_FOLDER/Import-$DATE/
convmv -f utf-8 -t utf-8 -r --notest --nfc $NEXTCLOUD_USER_FOLDER/*
sudo chown www-data:www-data -R $NEXTCLOUD_USER_FOLDER/*

# One of these two commands will work (because we do not know if the current nextcloud has apc.enable_cli=1 or not):
sudo -u www-data php $NEXTCLOUD_INSTALLATION_DIRECTORY/occ files:scan --all
rm nextcloud_import_process_running