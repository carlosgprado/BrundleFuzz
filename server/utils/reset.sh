#!/bin/bash

echo "##########################"
echo "# Reset to a clean state"
echo "##########################"

cd ..

echo "[*] Backing up logs"
mv logs/log.txt logs/log.txt.bak

echo "[*] Cleaning mutations"
rm -rf mutations
mkdir mutations

echo "[*] Populating samples"
rm -rf samples
mkdir samples

echo "[*] DONE."
echo "[*] Considering cleaning up the following directories"
echo "    * backup"
echo "    * crashes"
