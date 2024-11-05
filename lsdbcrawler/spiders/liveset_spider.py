import re
import dateparser
import scrapy
import urllib.parse

from scrapy.linkextractors import LinkExtractor
from scrapy import Request, exceptions
from scrapy.crawler import logger

from markdownify import markdownify

from lsdbcrawler.items import (
    LivesetItem,
    TrackItem,
    ArtistItem,
    GenreItem,
    TagItem,
    EventItem,
    UserItem,
    DownloadLinkItem,
    RaitingItem,
    FavoriteItem,
    CommentItem,
)

from lsdbcrawler.processors import to_int


set_submitted_regex = re.compile(
    r"Submitted by:\s+\[([^\[]+)\]\((.*)\)\s@\s(\d{2}-\d{2}-\d{4})\s(\d{2}:\d{2})",
    re.IGNORECASE,
)

set_edited_regex = re.compile(
    r"Last edited by:\s+\[([^\[]+)\]\((.*)\)\s@\s(\d{2}-\d{2}-\d{4})\s(\d{2}:\d{2})",
    re.IGNORECASE,
)

set_user_description_regex = re.compile(
    r"\n\*\*More info\*\*(.*)", flags=re.IGNORECASE | re.DOTALL
)

legacy_track_regex = re.compile(r"^(?P<index>\d{1,3})\s*[-.:]\s*(?P<song>.+?)$")


def defer_request(seconds: int, request: Request) -> Request:
    meta = dict(request.meta)
    meta.update({"__defer_delay": seconds})
    return request.replace(meta=meta)


class LivesetSpider(scrapy.Spider):
    name = "LivesetSpider"

    allowed_domains = ("lsdb.eu", "lsdb.nl")
    start_urls = ["https://lsdb.eu/livesets"]

    # url 'https://lsdb.eu/user/DJTheJoker' returns 500
    handle_httpstatus_list = [500]

    def __init__(self, *args, **kwargs):
        super(LivesetSpider, self).__init__(*args, **kwargs)

        if kwargs.get("start_urls"):
            self.start_urls = kwargs.get("start_urls").split(",")

        #self.allowed_domains = list(
        #    set(urllib.parse.urlparse(url).netloc for url in self.start_urls)
        #)

    def parse(self, response):
        raise exceptions.IgnoreRequest("")

    def start_requests(self):
        logger.info("Starting spider with urls %s", self.start_urls)

        for url in self.start_urls:
            page_type = urllib.parse.urlparse(url).path.split("/")[1]

            match page_type:
                case "livesets":
                    yield scrapy.Request(
                        url,
                        callback=self.parse_livesets_index,
                        dont_filter=True,
                    )
                case "set":
                    yield scrapy.Request(
                        url,
                        callback=self.parse_liveset,
                        dont_filter=True,
                    )

    def parse_livesets_index(self, response, **kwargs):
        """Parse the livesets index by going through each page and fetching the liveset urls."""
        current_page = self.get_current_page(response)
        next_page_url = self.get_next_page_url(response)

        is_restart = kwargs.get("restart", False)
        restart_count = kwargs.get("restart_count", 0)

        logger.info("Parsing livesets index page %s", current_page)
        if is_restart:
            logger.info("Restarting spider for page %s", response.url)
            if restart_count >= 5:
                logger.warning(
                    "Restart count exceeded, skipping page %s", response.url
                )
                yield from self.next_page(next_page_url, response)
                return
            else:
                restart_count += 1

        liveset_links = self.get_liveset_links(response)
        logger.info("Found %s livesets on page %s", len(liveset_links), current_page)

        if not liveset_links:
            logger.info("No livesets found on page %s (URL: %s)", current_page, response.url)
            yield self.next_page(next_page_url, response)
            return
    
        yield from self.process_liveset_links(liveset_links)

        if next_page_url:
            if not self.settings.get("DEBUG"):
                yield Request(
                    response.urljoin(next_page_url),
                    callback=self.parse_livesets_index,
                )
        else:
            logger.info("No more liveset pages found. Crawling finished.")

    def get_next_page_url(self, response):
        active_page = response.xpath("(//ul[@class='paging'])[1]/li[@class='active']") or None
        if not active_page:
            return None

        next_page = active_page.xpath(".//following-sibling::li[1]/a/@href") or None

        if not next_page:
            return None
        
        return next_page.extract_first()


    def get_current_page(self, response):
        active_page = response.xpath("(//ul[@class='paging'])[1]/li[@class='active']/a/text()") or None
        if not active_page:
            return None
        
        return active_page.extract_first()

    def get_liveset_links(self, response):
        return LinkExtractor(
            restrict_xpaths="(//ul[@class='setlist'])[1]//a", allow=r"/set/\d+"
        ).extract_links(response)

    def process_liveset_links(self, liveset_links):
        for idx, link in enumerate(liveset_links):
            if self.settings.get("DEBUG") and idx >= 1:
                break
            logger.info("Adding liveset to queue: %s", link.url)
            livesetlink = link.url + "?page=1"
            yield Request(livesetlink, callback=self.parse_liveset)

    def next_page(self, next_page_url, response, delay=None):
        if next_page_url:
            request = Request(
                response.urljoin(next_page_url),
                callback=self.parse_livesets_index,
            )
            if delay:
                yield defer_request(delay, request)
            else:
                yield request

    def parse_liveset(self, response):
        liveset_id = to_int(response.url.split("/")[4])

        logger.info("Parsing liveset ID %s", liveset_id)

        liveset_date = dateparser.parse(
            response.xpath(
                "//div[contains(@class, 'page_liveset')]//h1/time/@datetime"
            ).get()
        )

        event_info_tree = response.xpath("//div[contains(@class, 'page_liveset')]//h1")

        # Extract artists and separators
        artists = event_info_tree.xpath("a[starts-with(@href, '/artists/view/')]")

        separators = event_info_tree.xpath(
            "a[starts-with(@href, '/events/view/')]/preceding-sibling::text()[normalize-space()][not(contains(., '@'))]"
        ).getall()
        separators = [sep.strip() for sep in separators]
        # last artist does not have a separator so we add an empty one
        separators.append("")

        liveset_artists = list()
        for idx, (artist_obj, seperator) in enumerate(zip(artists, separators)):
            artist_item = ArtistItem()

            artist_text = artist_obj.xpath("./text()").get()
            artist_url = artist_obj.xpath("./@href").get()
            artist_id = artist_url.split("/")[3]

            artist_item["artist_id"] = int(artist_id)
            artist_item["name"] = str(artist_text).strip()

            liveset_artists.append({"artist": int(artist_id), "separator": seperator})

            yield artist_item

        # event information
        event_info = event_info_tree.xpath('a[starts-with(@href, "/events/view/")]')
        liveset_event_href = event_info.xpath("./@href").get()
        liveset_event_id = to_int(liveset_event_href.split("/")[3])
        liveset_event_name = str(event_info.xpath("./text()").get()).strip()
        event_item = EventItem()
        event_item["event_id"] = liveset_event_id
        event_item["name"] = liveset_event_name
        yield event_item

        liveset_title = (
            response.xpath(
                "//div[contains(@class, 'page_liveset')]//h1/a[last()]/following-sibling::text()[1]"
            )
            .get()
            .strip()
        )

        liveset_genres_urls = response.xpath(
            "//div[contains(@class, 'page_liveset')]/div[1]/a[contains(@href, '/genre/')]"
        )

        liveset_genres = list()
        for idx, url in enumerate(liveset_genres_urls):
            genre_item = GenreItem()

            genre_text = str(url.xpath("./text()").get()).strip()
            genre_url = url.xpath("./@href").get()
            genre_id = str(genre_url.split("/")[2]).strip()

            genre_item["genre_id"] = genre_id
            genre_item["name"] = genre_text

            liveset_genres.append(genre_id)

            yield genre_item

        liveset_tag_urls = response.xpath(
            "//div[contains(@class, 'page_liveset')]/div[1]/a[contains(@href, '/tag/')]"
        )

        livset_tags = list()
        for idx, url in enumerate(liveset_tag_urls):
            tag_item = TagItem()

            tag_text = str(url.xpath("./text()").get()).strip()
            tag_url = url.xpath("./@href").get()
            tag_id = str(tag_url.split("/")[2]).strip()

            tag_item["tag_id"] = tag_id
            tag_item["name"] = tag_text

            livset_tags.append(tag_id)

            yield tag_item

        liveset_likes = response.xpath(
            "//div[contains(@class, 'page_liveset')]//div[@class='rating_total']/text()"
        ).get()

        if liveset_likes:
            liveset_likes = to_int(
                str(liveset_likes).strip().replace("+", "").replace("-", "")
            )

        liveset_description_html = response.xpath(
            "//div[contains(@class, 'page_liveset')]/div[1]/div[1]/div[1]"
        ).get() or ""

        liveset_description_html_fixed = re.sub(
            r"\n\s+", " ", liveset_description_html.strip()
        )

        liveset_description_markdown = (
            markdownify(liveset_description_html_fixed).strip().replace(r"\_", "_")
        )

        liveset_submitted_list = re.match(
            set_submitted_regex, liveset_description_markdown
        )

        liveset_submitted_info = {}
        if liveset_submitted_list:
            (
                liveset_submitted_user,
                liveset_submitted_url,
                liveset_submitted_date,
                liveset_submitted_time,
            ) = liveset_submitted_list.groups(0)

            # note that LSDB does not store timestamp with timezone,
            # nor do the timezone change when browsing from another region. Force timezone
            liveset_submitted_fulldate = dateparser.parse(
                liveset_submitted_date + " " + liveset_submitted_time,
                settings={
                    "TIMEZONE": "Europe/Amsterdam",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "TO_TIMEZONE": "UTC",
                },
            )

            yield scrapy.Request(
                response.urljoin(liveset_submitted_url),
                callback=self.parse_user,
            )

            liveset_submitted_info = {
                "date": liveset_submitted_fulldate,
                "author": {
                    "href": response.urljoin(liveset_submitted_url),
                    "name": liveset_submitted_user,
                },
            }

        liveset_edited_list = re.search(set_edited_regex, liveset_description_markdown)

        liveset_edited_info = {}
        if liveset_edited_list:
            (
                liveset_edited_user,
                liveset_edited_url,
                liveset_edited_date,
                liveset_edited_time,
            ) = liveset_edited_list.groups()

            # note that LSDB does not store timestamp with timezone,
            # nor do the timezone change when browsing from another region. Force timezone
            liveset_edited_fulldate = dateparser.parse(
                liveset_edited_date + " " + liveset_edited_time,
                settings={
                    "TIMEZONE": "Europe/Amsterdam",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "TO_TIMEZONE": "UTC",
                },
            )

            yield scrapy.Request(
                response.urljoin(liveset_edited_url),
                callback=self.parse_user,
            )

            liveset_edited_info = {
                "date": liveset_edited_fulldate,
                "author": {
                    "href": response.urljoin(liveset_edited_url),
                    "name": liveset_edited_user.strip(),
                },
            }

        liveset_favorited_users = response.xpath(
            "//span[contains(@id, 'favorites_first') or contains(@id, 'favorites_all')]/a/@href"
        )

        for idx, user_url in enumerate(liveset_favorited_users):
            favorite_item = FavoriteItem()
            favorite_item["liveset_set_id"] = liveset_id
            favorite_item["user_name"] = user_url.get().split("/")[-1]
            yield favorite_item

        liveset_ratings = response.xpath(
            "//span[contains(@id, 'ratings_first') or contains(@id, 'ratings_all')]/a"
        )
        for idx, ratings in enumerate(liveset_ratings):
            rating_item = RaitingItem()
            rating = ratings.xpath("@class").get().split(" ")[1]
            rating_item["liveset_set_id"] = liveset_id
            rating_item["rating"] = to_int(rating.replace("rating-", ""))
            rating_item["user_name"] = ratings.xpath("@href").get().split("/")[-1]
            yield rating_item

        liveset_real_description_markdown = ""
        liveset_real_description_markdown_search = re.findall(
            set_user_description_regex, liveset_description_markdown
        )
        if liveset_real_description_markdown_search:
            liveset_real_description_markdown = re.sub(
                r"\s+(?=\n)", "", liveset_real_description_markdown_search[0].strip()
            )

        # detect tracklist type
        # if this is not None then we have modern else legacy
        tracklist_table_type_selector = response.xpath(
            "//div[contains(@class, 'page_liveset')]/div[1]/table"
        ).get()

        tracklist_type = None
        tracklist_data = []
        if tracklist_table_type_selector:
            tracklist_type = "modern"
            tracklist_data = self.parse_tracklist_modern(response)

            for track in tracklist_data:
                if track["track_type"] == "w" or track["track_type"] == "track":
                    track_item = TrackItem(
                        track_id=track["track_id"], track_name=track["track_name"]
                    )
                    yield track_item
                    del track["track_name"]
        else:
            tracklist_type = "old"
            tracklist_data = self.parse_tracklist_old(response)

        liveset_tracklist_info = {
            "type": tracklist_type,
            "tracks": tracklist_data,
        }

        # handle comments for liveset
        yield from self.parse_comments(response, liveset_id=liveset_id)

        # item info
        liveset = LivesetItem()
        liveset["set_id"] = liveset_id
        liveset["set_date"] = liveset_date
        liveset["artists"] = liveset_artists
        liveset["event_id"] = liveset_event_id
        liveset["episode"] = liveset_title
        liveset["genres"] = liveset_genres
        liveset["tags"] = livset_tags
        liveset["likes"] = liveset_likes
        liveset["submitted"] = liveset_submitted_info
        liveset["updated"] = liveset_edited_info
        liveset["description"] = liveset_real_description_markdown
        liveset["tracklist"] = liveset_tracklist_info
        liveset["download_ids"] = []
        liveset["original_url"] = response.url

        liveset_download_links = LinkExtractor(
            restrict_xpaths="/html/body/div[3]/div[1]/div[2]/div[2]//a",
            allow=r"/listen/go/\d+",
        ).extract_links(response)

        for link in liveset_download_links:
            yield Request(
                link.url,
                callback=self.parse_download_link,
                meta={"liveset": liveset},
            )
            download_id = to_int(link.url.split("/")[-1])
            liveset["download_ids"].append(download_id)

        yield liveset

    def parse_download_link(self, response):
        download_item = DownloadLinkItem()
        download_item["download_link_id"] = to_int(response.url.split("/")[-1])
        download_item["download_url"] = (
            response.xpath("//div/a[1]").xpath("@href").get()
        )
        download_item["liveset_set_id"] = response.meta["liveset"]["set_id"]

        yield download_item

    def parse_user(self, response):
        if response.status == 500:
            logger.warning("User page for user %s returned 500", response.url)
            # raise exceptions.IgnoreRequest("skipping user page")
            return
        user = UserItem()
        # grab userid using xpath to find x href that contains /messages/add?to=651
        user_message_href = response.xpath("//a[contains(@href, '/messages/add?to=')]")
        user_id = to_int(user_message_href.xpath("@href").get().split("=")[-1]) or 0
        user["user_id"] = user_id
        user["name"] = (
            response.xpath("/html/body/div[3]/div[1]/div/h1/text()").get().strip()
        )

        user_details = response.xpath("/html/body/div[3]/div[2]/div[1]").get()
        registered = re.search(r"(\d{4}|\d{2}-\d{2}-\d{4})", user_details)
        if registered:
            user["registered"] = dateparser.parse(registered.group())

        yield user

    def parse_comments(self, response, liveset_id=None):
        comments = response.xpath(
            "//div[contains(@class, 'container')]/div[4]/div[1]/div[contains(@class, 'comment')]"
        )[:-1]

        logger.debug("Found %s comments", len(comments))

        for idx, comment in enumerate(comments):
            comment_id = to_int(comment.xpath("@id").get().split("c")[-1])
            comment_head = comment.xpath("./div[1]")

            comment_user_href = comment_head.xpath(".//a[contains(@href, '/user/')]")
            comment_user_name = comment_user_href.xpath("@href").get().split("/")[-1]
            comment_date = comment.xpath(".//time/@datetime").get()
            comment_date = dateparser.parse(
                comment_date,
                settings={
                    "TIMEZONE": "Europe/Amsterdam",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "TO_TIMEZONE": "UTC",
                },
            )

            comment_body = comment.xpath("./div[2]")
            comment_text = comment_body.xpath("./div").get()
            comment_text = re.sub(r"\n\s+", "", comment_text.strip())
            comment_text = markdownify(comment_text.strip())

            comment_item = CommentItem()
            comment_item["comment_id"] = comment_id
            comment_item["user_name"] = comment_user_name
            comment_item["date"] = comment_date
            comment_item["text"] = comment_text
            comment_item["liveset_set_id"] = liveset_id

            yield comment_item

        next_page = response.xpath(
            "//ul[@class='paging']/li[@class='active']/following-sibling::li[1]/a/@href"
        ).get()

        if next_page and not self.settings.get("DEBUG"):
            yield scrapy.Request(
                response.urljoin(next_page),
                callback=self.parse_comments,
            )

    def parse_tracklist_modern(self, response):
        tracklist = response.xpath(
            "//div[contains(@class, 'page_liveset')]/div[1]/table//tr"
        )
        liveset_tracklist = []
        for idx, track in enumerate(tracklist):
            track_index = track.xpath("td[1]/text()").get()
            track_details = track.xpath("td[2]")
            # test if track is a song or a comment
            if track_details.xpath("a"):
                is_with_artist = track_details.xpath(
                    "text()[normalize-space()][contains(., 'w/')]"
                ).get()
                if not is_with_artist:
                    track_index = to_int(str(track_index).replace(".", "").strip())
                    track_name = track_details.xpath("a").xpath("text()").get()
                    track_href = track_details.xpath("a").xpath("@href").get()
                    track_id = to_int(track_href.split("/")[-2])
                    track_type = "track"
                else:
                    track_index = idx
                    track_name = track_details.xpath("a").xpath("text()").get()
                    track_href = track_details.xpath("a").xpath("@href").get()
                    track_id = to_int(track_href.split("/")[-2])
                    track_type = "w"
            else:
                track_index = idx
                track_id = 0
                track_is_id = track_details.xpath("text()[normalize-space()][1]").get()
                track_name = track_details.xpath("em/text()").get().strip()
                if track_is_id:
                    track_type = "ID"
                else:
                    track_type = "comment"

            liveset_tracklist.append(
                {
                    "track_id": track_id,
                    "track_name": track_name,
                    "track_type": track_type,
                }
            )
        return liveset_tracklist

    def parse_tracklist_old(self, response):
        tracklist = response.xpath(
            "//div[contains(@class, 'page_liveset')]/div[1]/h2/following-sibling::text()[normalize-space(.)]"
        ).getall()

        liveset_tracklist = []

        for idx, track in enumerate(tracklist):
            track = re.sub(r"\n\s+", " ", track.strip())

            # test if it's a track or comment by detecting the track index number #.
            is_track = legacy_track_regex.search(track)
            if is_track:
                track_index = is_track.group("index")
                track_name = is_track.group("song")
                track_type = "track"

            else:
                track_index = idx
                track_name = track.strip()
                if re.match(r"^ID\s?", track_name, flags=re.IGNORECASE):
                    # track_name = re.search(r"\((.*?)\)$", track_name).group(1)
                    track_type = "ID"
                else:
                    track_type = "comment"

            liveset_tracklist.append(
                {
                    "track_index": track_index,
                    "track_name": track_name,
                    "track_type": track_type,
                }
            )

        return liveset_tracklist
