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
