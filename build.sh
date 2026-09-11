#!/usr/bin/env bash
# Render build script. Configured as the Blueprint's buildCommand in render.yaml.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Uncomment to load clearly-labeled sample/demo data on first deploy:
# python manage.py seed_demo_data
