import dataclasses


@dataclasses.dataclass
class AudioFile:
    file: str
    volume: float = 1.0
    duck: bool = False
    metadata: dict = None
    _id: int = None
    guild: int = None
    title: str = None
    url: str = None

    def as_dict(self):
        return dataclasses.asdict(self)

    def as_markdown(self):
        return f"[{self.title}]({self.url})"

    def __eq__(self, other):
        if not isinstance(other, AudioFile):
            return False
        if self._id is not None and other._id is not None:
            return self._id == other._id
        if self.url is not None and other.url is not None:
            return self.url == other.url
        if self.title is not None and other.title is not None:
            return self.title == other.title
        return self.file == other.file