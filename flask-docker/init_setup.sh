
# first time configuration
if [ ! -d migrations ]; then
  flask db init &&
  flask db migrate -m "initial migrate" &&
  flask db upgrade
  flask create-type ADMIN &&
  flask create-type TOURIST &&
  flask create-type GUIDE &&
  flask create-profile -u admin -e admin@admin.com -p adminadmin123123 -f admin -l admin -t ADMIN
fi

flask run --host=0.0.0.0
