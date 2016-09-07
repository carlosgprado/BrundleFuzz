#!/bin/bash

echo "##########################"
echo "# Reset to a clean state"
echo "##########################"

cd /home/carlos/server

echo "[*] Backing up logs"
mv logs/log.txt logs/log.txt.bak

echo "[*] Cleaning mutations"
rm -rf mutations
mkdir mutations

echo "[*] Populating samples"
rm -rf samples
mkdir samples
cp /home/carlos/SHARED/SEEDS/OTHERS/PDF/*.pdf samples

echo "[*] DONE."
echo "[*] Considering cleaning up the following directories"
echo "    * backup"
echo "    * crashes"
