#!/bin/bash

PROJECT=
case "$CIRLCE_BRANCH" in
  "master")
  PROJECT=""
  ;;
  *)
  PROJECT="-$CIRLCE_BRANCH"
  ;;
esac

tar cvzf "shishito${PROJECT}.tgz" * .[^.]*

# scp "shishito${PROJECT}.tgz" root@qa.salsitasoft.com:/usr/share/nginx/html/qa/
