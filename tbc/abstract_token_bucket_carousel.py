from abc import ABC, abstractmethod
from typing import NewType

Model = NewType("Model", str)
Region = NewType("Region", str)


class TokenBucketCarousel(ABC):
    """Abstract base class for a token bucket carousel"""

    @abstractmethod
    async def list_models(self) -> set[Model]:
        """List all models in the carousel

        Raises:
            NotImplementedError: _description_

        Returns:
            set[Model]: _description_
        """
        raise NotImplementedError

    @abstractmethod
    async def list_model_regions(self, model: Model) -> set[Region]:
        """List all regions for a model

        Args:
            model (Model): _description_

        Raises:
            NotImplementedError: _description_

        Returns:
            set[Region]: _description_
        """
        raise NotImplementedError

    @abstractmethod
    async def create_model_region(
        self,
        model: Model,
        region: Region,
        token_allowance: int,
        token_refresh_seconds: int,
        meta: dict,
    ):
        """Create a new region for a model

        Args:
            model (Model): The model to create a region for
            region (Region): The region to create
            token_allowance (int): Number of tokens in the bucket
            token_refresh_seconds (int): Time in seconds to refresh tokens
            meta (dict): metauration for the region

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError

    @abstractmethod
    async def read_model_region(self, model: Model, region: Region):
        """Read the current state of a region

        Args:
            model (Model): The model to read
            region (Region): The region to read

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError

    @abstractmethod
    async def update_model_region(
        self,
        model: Model,
        region: Region,
        token_allowance: int,
        token_refresh_seconds: int,
        meta: dict,
    ):
        """Update the metauration of a region

        Args:
            model (Model): The model to update
            region (Region): The region to update
            token_allowance (int): Number of tokens in the bucket
            token_refresh_seconds (int): Time in seconds to refresh tokens
            meta (dict): metauration for the region

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError

    async def delete_model_region(self, model: Model, region: Region):
        """Delete a region

        Args:
            model (Model): The model of the region to delete
            region (Region): The region to delete

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError

    @abstractmethod
    async def replenish_tokens(self, model: Model, region: Region):
        """Replenish tokens in the carousel

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError

    @abstractmethod
    async def request_tokens(
        self,
        model: Model,
        required_tokens: int,
        fallback_models: set[Model],
        allowed_regions: set[Region],
    ):
        """Request tokens from the carousel

        Args:
            model (Model): The model to request tokens for
            required_tokens (int): Number of tokens required
            fallback_models (set[Model]): Models to fallback to if the requested model does not have enough tokens
            allowed_regions (set[Region]): Regions to request tokens from

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError
