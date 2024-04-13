#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done

echo "PostgreSQL started"

#python manage.py flush --no-input
python manage.py migrate --no-input
#python manage.py collectstatic --no-input
#python manage.py loaddata ./db.json
#python manage.py shell < ./config/create_superuser.py

exec "$@"