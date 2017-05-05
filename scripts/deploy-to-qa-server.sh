#!/bin/bash

set -x

tar cvzf "shishito-${CIRCLE_BRANCH}.tgz" requirements setup.py pytest_imports shi shi.py shishito

scp "shishito-${CIRCLE_BRANCH}.tgz" root@qa.salsitasoft.com:/usr/share/nginx/html/qa/
