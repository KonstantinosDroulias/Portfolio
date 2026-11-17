#!/usr/bin/env bash
# Nightly: SQLite snapshot + uploaded files. Keeps 14 days. Run by /etc/cron.d/konstantinosdroulias.
set -euo pipefail
B=/srv/konstantinosdroulias/backups; D=/srv/konstantinosdroulias/data; T=$(date +%F)
mkdir -p "$B"
sqlite3 "$D/db.sqlite3" ".backup '$B/db-$T.sqlite3'"
gzip -f "$B/db-$T.sqlite3"
tar -czf "$B/media-$T.tar.gz" -C "$D" media
find "$B" -type f -mtime +14 -delete
# Privacy policy: contact messages are kept 24 months at most.
sudo -u kd bash -c "set -a; . /srv/konstantinosdroulias/.env; set +a; cd /srv/konstantinosdroulias/app && /srv/konstantinosdroulias/venv/bin/python manage.py prune_messages"
