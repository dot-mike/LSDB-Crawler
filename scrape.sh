#!/usr/bin/env bash

URL="${1:-https://lsdb.eu/livesets}"

TZ=$(cat /etc/timezone)

set -euo pipefail

docker network ls | grep lsdb-crawler-network || \
    docker network create lsdb-crawler-network

# start the stack (mongodb)
docker-compose up -d

# build the docker image for the spider
docker build -t lsdb-crawler -f Dockerfile .

# run the docker image to start the spider
docker run -d --rm --name lsdb-crawler-app \
    -v "$(pwd)/proxies.txt:/app/data/proxies.txt" \
    -v "$(pwd)/data:/data" \
    -e MONGO_DATABASE="lsdb" \
    -e MONGO_URI=mongodb://root:password@lsdb-crawler-db:27017 \
    -e PROXY_FILE=/app/data/proxies.txt \
    -e LOG_FILE="/data/lsdb_crawler.log" \
    --network lsdb-crawler-network \
    lsdb-crawler

echo -e "Started crawler lsdb-crawler-app. Run 'docker logs -f lsdb-crawler-app' to see the logs.\nTo stop the crawler, run 'docker stop lsdb-crawler-app'"
