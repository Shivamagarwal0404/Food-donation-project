#!/bin/bash
# =============================================================================
# FoodShare — Production RDS Bootstrap Script
# Execute this script on the EC2 instance during production deployment
# BEFORE running python manage.py migrate.
#
# This script:
# 1. Connects to the RDS PostgreSQL database (foodshare_db)
# 2. Creates the 'foodshare' schema if it does not already exist
# 3. Executes Django migrations into the foodshare schema
# 4. Collects static files for Nginx
# =============================================================================
set -e

echo "=== Step 1: Initializing RDS PostgreSQL 'foodshare' schema ==="
python manage.py init_prod_schema

echo "=== Step 2: Running Django migrations ==="
python manage.py migrate

echo "=== Step 3: Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Production Database Bootstrap Complete ==="

