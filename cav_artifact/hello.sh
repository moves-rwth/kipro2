#!/bin/bash

cat /root/artifact/cav_artifact/README.md

echo
echo "You are now in /root/artifact."
echo

cd /root/artifact

exec bash -l -c "poetry run bash"
