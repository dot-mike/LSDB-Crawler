import pymongo
import datetime
from scrapy.exceptions import DropItem, NotConfigured

import logging
logger = logging.getLogger(__name__)

class MongoPipeline(object):
    def __init__(self, settings, stats, **kwargs):
        self.stats = stats
        if not settings.get('MONGODB_DATABASE'):
            raise NotConfigured
        if not settings.get('MONGODB_URI'):
            raise NotConfigured('MONGODB_URI is not set')

        self._uri = settings.get('MONGODB_URI', 'mongodb://localhost:27017')
        self._database = settings.get('MONGODB_DATABASE')
            
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings, crawler.stats)

    def open_spider(self, spider):
        self.connection = pymongo.MongoClient(self._uri)
        self.database = self.connection[self._database]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # filter based on item's unique fields
        filter_dict = {key: item[key] for key in item if key in item.unique_fields}

        # append a "last_modified" datetime field.
        insert_dict = dict(item)
        insert_dict.update({"last_modified": datetime.datetime.now(datetime.timezone.utc)})

        # update or insert (aka "upsert") with the $set field update operator
        try:
            self.database[item.collection].update_one(
                filter_dict, {"$set": insert_dict}, upsert=True
            )
        except pymongo.errors.PyMongoError as e:
            spider.logger.error(f"Database error: {e}")
            raise DropItem(f"Database error: {e}")

        return item
