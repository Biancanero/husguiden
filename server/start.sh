#!/bin/sh
# Container entry: SITE = a folder in dist/ (family, husbok-palma, husbok-<id>, or . for everything),
# SEED = space-separated houses/<dir>[:prefix] that fill an EMPTY database on first start.
set -e
args=""
for s in $SEED; do args="$args --seed $s"; done
[ -n "$EXAMPLE_PRIVATE" ] && args="$args --example-private db/examples/private.example.json"
exec python3 -I server/server.py --site "dist/${SITE:-family}" --db "/data/${DB_NAME:-husguiden}.sqlite" $args
