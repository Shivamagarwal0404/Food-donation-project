# =============================================================================
# FoodShare — Gunicorn configuration (production)
# Used by: gunicorn config.wsgi:application -c gunicorn.conf.py
# =============================================================================

import multiprocessing

# Binding
bind = "0.0.0.0:8000"

# Workers — 2 workers suitable for t3.small (2 vCPUs, 2GB RAM)
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"       # stdout
errorlog  = "-"       # stderr
loglevel  = "info"

# Process naming
proc_name = "foodshare"

# Graceful restart timeout
graceful_timeout = 30
