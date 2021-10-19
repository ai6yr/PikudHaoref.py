import asyncio
import time
from datetime import datetime
from threading import Thread
from typing import Union, List

from .city import City
from .base import EventManager
from .http import SyncHTTPClient, ASyncHTTPClient
from .siren import Siren

__all__ = ("SyncClient", "ASyncClient")


class SyncClient(EventManager):
    """
    Represents a sync pikudhaoref client.
    """

    __slots__ = ("closed", "http", "update_interval", "_known_sirens")

    def __init__(self, update_interval: Union[int, float] = 2):
        """
        :param Union[int, float] update_interval: The update interval of the client.
        """

        super().__init__()

        self.closed = False
        self.http = SyncHTTPClient()

        self.update_interval = update_interval
        self._known_sirens = []

        Thread(target=self._handle_sirens).start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.closed = True
        self.http.session.close()

    @property
    def history(self) -> List[Siren]:
        return [Siren.from_raw(x) for x in self.http.get_history()]

    @property
    def current_sirens(self) -> List[Siren]:
        return [
            Siren(City.from_city_name(x), datetime.utcnow())
            for x in self.http.get_current_sirens()
        ]

    def _handle_sirens(self):
        while not self.closed:
            time.sleep(self.update_interval)
            cities = self.http.get_current_sirens()

            if cities:
                new_cities = [city for city in cities if city not in self._known_sirens]
                if new_cities:
                    self.call_sync_event("on_siren", new_cities)

                ended_sirens = [x for x in self._known_sirens if x not in cities]
                if ended_sirens:
                    self.call_sync_event("on_siren_end", ended_sirens)

                self._known_sirens = cities
            else:
                self._known_sirens = []


class ASyncClient(EventManager):
    """
    Represents an async pikudhaoref client.
    """

    __slots__ = ("closed", "http", "update_interval", "_known_sirens", "loop")

    def __init__(
        self, update_interval: Union[int, float] = 2, loop: asyncio.BaseEventLoop = None
    ):
        """
        :param Union[int, float] update_interval: The update interval of the client.
        """

        super().__init__()

        self.loop = loop or asyncio.get_event_loop()
        self.closed = False
        self.http = ASyncHTTPClient(loop=loop)

        self.update_interval = update_interval
        self._known_sirens = []

        loop.create_task(self._handle_sirens())

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        self.closed = True
        await self.http.session.close()

    async def history(self) -> List[Siren]:
        return [Siren.from_raw(x) for x in await self.http.get_history()]

    async def current_sirens(self) -> List[Siren]:
        return [
            Siren(City.from_city_name(x), datetime.utcnow())
            for x in await self.http.get_current_sirens()
        ]

    async def _handle_sirens(self):
        while not self.closed:
            await asyncio.sleep(self.update_interval)
            cities = await self.http.get_current_sirens()

            if cities:
                new_cities = [city for city in cities if city not in self._known_sirens]
                if new_cities:
                    await self.call_async_event("on_siren", new_cities)

                ended_sirens = [x for x in self._known_sirens if x not in cities]
                if ended_sirens:
                    await self.call_async_event("on_siren_end", ended_sirens)

                self._known_sirens = cities
            else:
                self._known_sirens = []
