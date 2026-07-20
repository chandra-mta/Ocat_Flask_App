#!/bin/bash

SOURCE_DIR="$(dirname "${BASH_SOURCE[0]}")"

case "$1" in
  prod)
    APP_ROOT=/proj/web-cxc/wsgi-scripts/cus
    CONFIG_NAME=cxcweb
    ;;
  test)
    APP_ROOT=/proj/web-cxc-dmz-test/wsgi-scripts/cus
    CONFIG_NAME=cxctest
    ;;
  r2d2)
    APP_ROOT=/proj/web-r2d2-v/wsgi-scripts/cus
    CONFIG_NAME=r2d2
    ;;
  home)
    APP_ROOT="$HOME/cus"
    CONFIG_NAME=localhost
    ;;
  *)
    echo "Usage: $0 {prod|test|r2d2|home}"
    exit 1
    ;;
esac

#: Make the APP_ROOT directory if it doesn't exist. (only for home setting)
mkdir -p $APP_ROOT
#: Replace the _CONFIGURATION_NAME in the usint file with the appropriate value for the selected environment
sed "s|_CONFIGURATION_NAME = \"localhost\"|_CONFIGURATION_NAME = \"$CONFIG_NAME\"|" "$SOURCE_DIR/usint" > "$APP_ROOT/usint"
chmod 755 "$APP_ROOT/usint"
#: Replace the rest of the files.
cp -f "$SOURCE_DIR/config.py" "$APP_ROOT/"
rsync -av --delete "$SOURCE_DIR/cus_app/" "$APP_ROOT/cus_app/"
rsync -av --delete "$SOURCE_DIR/other_scripts/" "$APP_ROOT/other_scripts/"