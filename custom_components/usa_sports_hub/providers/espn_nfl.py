from .espn import EspnProvider
class NflProvider(EspnProvider):
    def __init__(self, session): super().__init__(session,"football/nfl","nfl","NFL")
