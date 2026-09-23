from .espn import EspnProvider
class NbaProvider(EspnProvider):
    def __init__(self, session): super().__init__(session,"basketball/nba","nba","NBA")
