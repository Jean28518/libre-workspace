#!/bin/bash


# cd /root/onlyoffice

# docker rm -f onlyoffice
# bash run.sh

# We remove and install onlyoffice again, because sometimes the onlyoffice integration in nextcloud stops silently working
. ../env.sh
. ../onlyoffice/remove_onlyoffice.sh

cd /usr/share/linux-arbeitsplatz/unix/unix_scripts/onlyoffice
. ./setup_onlyoffice.sh
cd /usr/share/linux-arbeitsplatz/unix/unix_scripts/maintenance