#!/bin/sh

cd /app/ || exit

export DEBUG=1
export LOG_LEVEL=DEBUG

nohup scrapy crawl LivesetSpider
# allow time for the spider to start and create log file
sleep 2
tail -f "$LOG_FILE"