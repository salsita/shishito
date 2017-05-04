#!/bin/bash

set -x

tar cvzf "shishito-${CIRCLE_BRANCH}.tgz" * .[^.]*

scp "shishito${CIRCLE_BRANCH}.tgz" root@qa.salsitasoft.com:/usr/share/nginx/html/qa/
