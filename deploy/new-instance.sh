#!/bin/sh
# Creates and starts one more independent house guide.
#   sh deploy/new-instance.sh <name> <site> <seed> <port>
#   sh deploy/new-instance.sh villa-ek husbok-villaek houses/villaek 8102
# Writes instances/<name>.env with a random owner password (printed once), then starts Compose project <name>.
set -e
[ $# -eq 4 ] || { echo "usage: $0 <name> <site> <seed> <port>"; exit 1; }
name=$1; site=$2; seed=$3; port=$4
mkdir -p instances
f=instances/$name.env
[ -e "$f" ] && { echo "$f exists"; exit 1; }
pw=$(python3 -c "import secrets;print(secrets.token_urlsafe(12))")
sed -e "s|^SITE=.*|SITE=$site|" -e "s|^SEED=.*|SEED=$seed|" -e "s|^PORT=.*|PORT=$port|" -e "s|^OWNER_PASSWORD=.*|OWNER_PASSWORD=$pw|" deploy/instance.env.example > "$f"
chmod 600 "$f"
docker compose -p "$name" --env-file "$f" up -d --build
echo "started $name on port $port – owner password: $pw (also in $f)"
