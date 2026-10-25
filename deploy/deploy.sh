#!/bin/bash
# Run from any directory: sudo bash /path/to/cloud-cafe/deploy/deploy.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

if [[ $EUID -ne 0 ]]; then
    echo "Please run this script with sudo." >&2
    exit 1
fi
. /etc/os-release
if [[ "$ID" != ubuntu || "$VERSION_ID" != 22.04 ]]; then
    echo "This installer targets Ubuntu 22.04 LTS." >&2
    exit 1
fi

SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR=/opt/cloud-cafe
for file in app.py menu.py requirements.txt templates/index.html static/style.css static/script.js static/cafe.svg deploy/cloud-cafe.service; do
    if [[ ! -f "$SOURCE_DIR/$file" ]]; then
        echo "Missing project file: $file" >&2
        exit 1
    fi
done

apt-get -o DPkg::Lock::Timeout=180 -o Acquire::Retries=3 update
apt-get -o DPkg::Lock::Timeout=180 -o Acquire::Retries=3 install -y python3 python3-venv ca-certificates curl

if ! getent group cloud-cafe >/dev/null; then
    groupadd --system cloud-cafe
fi
if ! id -u cloud-cafe >/dev/null 2>&1; then
    useradd --system --gid cloud-cafe --home-dir /nonexistent --no-create-home --shell /usr/sbin/nologin cloud-cafe
fi

install -d -m 0755 "$APP_DIR" "$APP_DIR/templates" "$APP_DIR/static"
for file in app.py menu.py requirements.txt templates/index.html static/style.css static/script.js static/cafe.svg; do
    install -o root -g root -m 0644 "$SOURCE_DIR/$file" "$APP_DIR/$file"
done
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install --disable-pip-version-check -r "$APP_DIR/requirements.txt"
"$APP_DIR/.venv/bin/python" -m pip check

# Preserve the teacher's optional display settings when rerunning the installer.
if [[ ! -f /etc/cloud-cafe.env ]]; then
    cat > /etc/cloud-cafe.env <<'CLOUD_CAFE_ENV'
APP_VERSION=1.0
# Leave SERVER_NAME unset to show each instance's real hostname.
# SERVER_NAME=Alain-demo
CLOUD_CAFE_ENV
fi
chown root:root /etc/cloud-cafe.env
chmod 0640 /etc/cloud-cafe.env
install -o root -g root -m 0644 "$SOURCE_DIR/deploy/cloud-cafe.service" /etc/systemd/system/cloud-cafe.service
systemctl daemon-reload
systemctl enable cloud-cafe
systemctl restart cloud-cafe

for attempt in {1..30}; do
    if [[ "$(curl --fail --silent --max-time 2 http://127.0.0.1:8080/health || true)" == OK ]]; then
        echo "Cloud Cafe is ready on port 8080. Health check: OK"
        exit 0
    fi
    sleep 1
done
echo "Health check failed. Run: sudo journalctl -u cloud-cafe -n 80 --no-pager" >&2
exit 1
