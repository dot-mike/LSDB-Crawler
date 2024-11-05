import scrapy
from pprint import pformat

class BaseItem(scrapy.Item):
    unique_fields = None
    collection = None

    def __init__(self, *args, **kwargs):
        super(BaseItem, self).__init__(*args, **kwargs)

        if self.unique_fields is None:
            raise NotImplementedError(
                f"'unique_fields' not defined in {self.__class__.__name__}"
            )

        if self.collection is None:
            raise NotImplementedError(
                f"'collection' not defined in {self.__class__.__name__}"
            )

        if not isinstance(self.unique_fields, list):
            raise TypeError(
                f"'unique_fields' must be a list in {self.__class__.__name__}"
            )

        if not isinstance(self.collection, str):
            raise TypeError(
                f"'collection' must be a string in {self.__class__.__name__}"
            )

class LivesetItem(BaseItem):
    collection = "liveset"
    unique_fields = ["set_id"]

    set_id = scrapy.Field()
    set_date = scrapy.Field()
    artists = scrapy.Field()
    event_id = scrapy.Field()
    genres = scrapy.Field()
    tags = scrapy.Field()
    episode = scrapy.Field()
    likes = scrapy.Field()
    submitter = scrapy.Field()
    edited_by = scrapy.Field()
    submitted = scrapy.Field()
    updated = scrapy.Field()
    description = scrapy.Field()
    tracklist = scrapy.Field()
    download_ids = scrapy.Field()
    original_url = scrapy.Field()
    favorited = scrapy.Field()
    rated = scrapy.Field()

    def __repr__(self):
        return repr({"set_id": self["set_id"]})


class TrackItem(BaseItem):
    collection = "track"
    unique_fields = ["track_id"]

    track_id = scrapy.Field()
    track_name = scrapy.Field()


class ArtistItem(BaseItem):
    collection = "artist"
    unique_fields = ["artist_id"]

    artist_id = scrapy.Field()
    name = scrapy.Field()


class GenreItem(BaseItem):
    collection = "genre"
    unique_fields = ["genre_id"]

    genre_id = scrapy.Field()
    name = scrapy.Field()


class TagItem(BaseItem):
    collection = "tag"
    unique_fields = ["tag_id"]

    tag_id = scrapy.Field()
    name = scrapy.Field()


class EventItem(BaseItem):
    collection = "event"
    unique_fields = ["event_id"]

    event_id = scrapy.Field()
    name = scrapy.Field()


class UserItem(BaseItem):
    collection = "user"
    unique_fields = ["user_id"]

    user_id = scrapy.Field()
    name = scrapy.Field()
    registered = scrapy.Field()
    avatar = scrapy.Field()

    def __repr__(self):
        return repr({"user_id": self["user_id"]})


class DownloadLinkItem(BaseItem):
    collection = "download_link"
    unique_fields = ["download_link_id"]

    download_link_id = scrapy.Field()
    liveset_set_id = scrapy.Field()
    download_url = scrapy.Field()

    def __repr__(self):
        return repr({"download_link_id": self["download_link_id"]})


class RaitingItem(BaseItem):
    collection = "rating"
    unique_fields = ["liveset_set_id", "user_name"]

    liveset_set_id = scrapy.Field()
    user_name = scrapy.Field()
    rating = scrapy.Field()


class FavoriteItem(BaseItem):
    collection = "favorite"
    unique_fields = ["liveset_set_id", "user_name"]

    liveset_set_id = scrapy.Field()
    user_name = scrapy.Field()


class CommentItem(BaseItem):
    collection = "comment"
    unique_fields = ["comment_id"]

    comment_id = scrapy.Field()
    liveset_set_id = scrapy.Field()
    user_name = scrapy.Field()
    date = scrapy.Field()
    text = scrapy.Field()

    def __repr__(self):
        return repr({"comment_id": self["comment_id"]})


class FailedRequestItem(BaseItem):
    collection = "failed_request"
    unique_fields = ["url"]

    url = scrapy.Field()
    status = scrapy.Field()
    meta = scrapy.Field()
