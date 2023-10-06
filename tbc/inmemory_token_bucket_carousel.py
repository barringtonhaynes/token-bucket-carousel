from .abstract_token_bucket_carousel import Model, Region, TokenBucketCarousel
from .errors import InvalidModelError, InvalidRegionError


class InMemoryTokenBucketCarousel(TokenBucketCarousel):
    def __init__(self):
        self.models = {}

    async def list_models(self) -> set[Model]:
        return set(self.models.keys())

    async def list_model_regions(self, model: Model) -> set[Region]:
        try:
            return set(self.models[model].keys())
        except KeyError as err:
            raise InvalidModelError(f"Model {model} does not exist") from err

    async def create_model_region(
        self,
        model: Model,
        region: Region,
        token_allowance: int,
        token_refresh_seconds: int,
        meta: dict,
    ):
        if model not in self.models:
            self.models[model] = {}
        if region in self.models[model]:
            raise ValueError(f"Model {model} already has region {region}")
        self.models[model][region] = {
            "token_allowance": token_allowance,
            "token_refresh_seconds": token_refresh_seconds,
            "meta": meta,
            "tokens": token_allowance,
            "last_refresh": None,
        }

    async def read_model_region(self, model: Model, region: Region):
        if model not in self.models:
            raise InvalidModelError(f"Model {model} does not exist")
        if region not in self.models[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        return self.models[model][region]

    async def update_model_region(
        self,
        model: Model,
        region: Region,
        token_allowance: int,
        token_refresh_seconds: int,
        meta: dict,
    ):
        if model not in self.models:
            raise InvalidModelError(f"Model {model} does not exist")
        if region not in self.models[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        self.models[model][region] = {
            "token_allowance": token_allowance,
            "token_refresh_seconds": token_refresh_seconds,
            "meta": meta,
            "tokens": token_allowance,
            "last_refresh": None,
        }

    async def delete_model_region(self, model: Model, region: Region):
        if model not in self.models:
            raise InvalidModelError(f"Model {model} does not exist")
        if region not in self.models[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        del self.models[model][region]

    async def replenish_tokens(self, model: Model, region: Region):
        if model not in self.models:
            raise InvalidModelError(f"Model {model} does not exist")
        if region not in self.models[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        self.models[model][region]["tokens"] = self.models[model][region][
            "token_allowance"
        ]

    async def request_tokens(
        self, model: Model, required_tokens: int, fallback_models: int, allowed_regions
    ):
        if model not in self.models:
            raise InvalidModelError(f"Model {model} does not exist")
        if len(allowed_regions) == 0:
            allowed_regions = set(self.models[model].keys())
        for region in allowed_regions:
            if region not in self.models[model]:
                raise InvalidRegionError(f"Model {model} does not have region {region}")
        if model not in self.models:
            raise InvalidModelError(f"Model {model} does not exist")