#!/bin/bash

set -x

tar cvzf "shishito-${CIRCLE_BRANCH}.tgz" shishito/ requirements setup.py

scp "shishito-${CIRCLE_BRANCH}.tgz" root@qa.salsitasoft.com:/usr/share/nginx/html/qa/
