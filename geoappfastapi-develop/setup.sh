#!/bin/bash
heroku addons:create heroku-postgresql:hobby-dev
heroku pg:psql -c "CREATE EXTENSION postgis;" 