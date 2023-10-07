from tbc.abstract_token_bucket_carousel import Model, Region, TokenBucketCarousel
from tbc.errors import InvalidModelError, InvalidRegionError


class InMemoryTokenBucketCarousel(TokenBucketCarousel):
    def __init__(self):
        self.models = {}

    def list_models(self) -> set[Model]:
        return set(self.models.keys())

    def list_model_regions(self, model: Model) -> set[Region]:
        try:
            return set(self.models[model].keys())
        except KeyError as err:
            raise InvalidModelError(f"Model {model} does not exist") from err

    def create_model_region(
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
            "tokens_remaining": token_allowance,
            "last_refresh": self._current_time(),
        }

    def read_model_region(self, model: Model, region: Region):
        if model not in self.models or region not in self.models[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        return self.models[model][region]

    def update_model_region(
        self,
        model: Model,
        region: Region,
        token_allowance: int,
        token_refresh_seconds: int,
        meta: dict,
    ):
        if model not in self.models or region not in self.models[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        self.models[model][region]["token_allowance"] = token_allowance
        self.models[model][region]["token_refresh_seconds"] = token_refresh_seconds
        self.models[model][region]["meta"] = meta

    def delete_model_region(self, model: Model, region: Region):
        if model not in self.models or region not in self.models[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        del self.models[model][region]

    def replenish_tokens(self, model: Model, region: Region):
        if model not in self.models or region not in self.models[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        self.models[model][region]["tokens_remaining"] = self.models[model][region][
            "token_allowance"
        ]
        self.models[model][region]["last_refresh"] = self._current_time()

    async def request_tokens(
        self,
        model: Model,
        required_tokens: int,
        fallback_models: set[Model],
        allowed_regions: set[Region],
        preferred_region: Region,
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
