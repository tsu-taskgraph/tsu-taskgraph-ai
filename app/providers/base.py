from abc import ABC, abstractmethod
from typing import Any

from app.schemas.common import ProviderConfig


class BaseProvider(ABC):

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    async def check(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def generate_skeleton(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def enrich_task(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def mutate_graph(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def smart_recovery(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def generate_diagrams(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def generate_wiki(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        ...
