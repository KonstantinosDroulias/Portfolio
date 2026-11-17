#!/usr/bin/env bash
# Deploy to the VPS: rsync code, install requirements, migrate, collect static, restart.
set -euo pipefail
cd "$(dirname "$0")/.."
H=root@drouliasvps.cloud
R=/srv/konstantinosdroulias
rsync -az --delete --exclude .git --exclude .venv --exclude data --exclude '__pycache__' --exclude .env --exclude '.DS_Store' ./ "$H:$R/app/"
ssh "$H" bash -s <<REMOTE
set -euo pipefail
chown -R kd:www-data $R/app
sudo -u kd $R/venv/bin/pip install -q -r $R/app/requirements.txt
cd $R/app
sudo -u kd bash -c "set -a; . $R/.env; set +a; $R/venv/bin/python manage.py migrate --noinput -v0 && $R/venv/bin/python manage.py collectstatic --noinput -v0"
install -m 755 $R/app/deploy/backup.sh /usr/local/bin/konstantinosdroulias-backup
systemctl restart konstantinosdroulias
sleep 2
curl -fsS -o /dev/null -w "home %{http_code}\n" https://konstantinosdroulias.com/
REMOTE
