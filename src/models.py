from typing import Optional, Union, TypeVar, Type
from datetime import datetime
from dataclasses import dataclass, field

_T = TypeVar("_T")


@dataclass
class Board:
    name: str
    short: str
    username: Optional[str] = None
    description: Optional[str] = None
    thread_posts: Optional[int] = 5
    thread_bump: Optional[int] = 10
    thread_catalog: Optional[int] = 10
    country: bool = False
    custom: bool = False
    roll: bool = False
    unlisted: bool = False
    postcount: int = 0
    mediacount: int = 0
    created: datetime = datetime.utcnow()
    banners: list[str] = field(default_factory=list)
    perpage: int = 10
    pinned: Optional[int] = None

    @classmethod
    def from_mongo_document(cls: Type[_T], data: dict[str, Union[str, int, datetime]]) -> _T:
        # TODO: implement data processing
        return Board(**data)

    @classmethod
    def from_dict(cls: Type[_T], data: dict[str, Union[str, int]]) -> _T:
        # TODO: add validation ?
        return Board(
            name=data.get("name"),
            short=data.get("short"),
            username=data.get("username", "Anon"),
            description=data.get("description", ""),
            thread_posts=data.get("thread_posts", 15),
            thread_bump=data.get("thread_bump", 10),
            thread_catalog=data.get("thread_catalog", 10),
            country=data.get("country", False),
            custom=data.get("custom", False),
            roll=data.get("roll", False),
            unlisted=data.get("unlisted", False),
            postcount=data.get("postcount", 0),
            mediacount=data.get("mediacount", 0),
            created=data.get("created", datetime.utcnow()),
            banners=data.get("banners", []),
            perpage=data.get("perpage", 10),
            pinned=data.get("pinned", None),
        )

    def add_banner(self, banner: str):
        self.banners.append(banner)

    # this enables the dict() method to be called upon the class
    def __iter__(self):
        yield "name", self.name
        yield "short", self.short
        yield "username", self.username
        yield "description", self.description
        yield "thread_posts", self.thread_posts
        yield "thread_bump", self.thread_bump
        yield "thread_catalog", self.thread_catalog
        yield "country", self.country
        yield "custom", self.custom
        yield "roll", self.roll
        yield "unlisted", self.unlisted
        yield "postcount", self.postcount
        yield "mediacount", self.mediacount
        yield "created", self.created
        yield "banners", self.banners
        yield "perpage", self.perpage
        yield "pinned", self.pinned
