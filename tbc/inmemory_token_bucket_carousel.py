from tbc.abstract_token_bucket_carousel import Model, Region, TokenBucketCarousel
from tbc.errors import InvalidModelError, InvalidRegionError


class InMemoryTokenBucketCarousel(TokenBucketCarousel):
    def __init__(self):
        super().__init__()
        self.__data = {}

    def list_models(self) -> set[Model]:
        return set(self.__data.keys())

    def list_model_regions(self, model: Model) -> set[Region]:
        try:
            return set(self.__data[model].keys())
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
        if model not in self.__data:
            self.__data[model] = {}
        if region in self.__data[model]:
            raise ValueError(f"Model {model} already has region {region}")
        self.__data[model][region] = {
            "token_allowance": token_allowance,
            "token_refresh_seconds": token_refresh_seconds,
            "meta": meta,
            "tokens_remaining": token_allowance,
            "last_refresh": self._current_time(),
        }

    def read_model_region(self, model: Model, region: Region):
        if model not in self.__data or region not in self.__data[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        return self.__data[model][region]

    def update_model_region(
        self,
        model: Model,
        region: Region,
        token_allowance: int,
        token_refresh_seconds: int,
        meta: dict,
    ):
        if model not in self.__data or region not in self.__data[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        self.__data[model][region]["token_allowance"] = token_allowance
        self.__data[model][region]["token_refresh_seconds"] = token_refresh_seconds
        self.__data[model][region]["meta"] = meta

    def delete_model_region(self, model: Model, region: Region):
        if model not in self.__data or region not in self.__data[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        del self.__data[model][region]

    def replenish_tokens(self, model: Model, region: Region):
        if model not in self.__data or region not in self.__data[model]:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        self.__data[model][region]["tokens_remaining"] = self.__data[model][region][
            "token_allowance"
        ]
        self.__data[model][region]["last_refresh"] = self._current_time()

    async def request_tokens(
        self,
        model: Model,
        required_tokens: int,
        fallback_models: set[Model] = None,
        allowed_regions: set[Region] = None,
        preferred_region: Region = None,
    ) -> dict:
        region = None
        if model not in self.__data:
            raise InvalidModelError(f"Model {model} does not exist")
        if allowed_regions is None or len(allowed_regions) == 0:
            allowed_regions = set(self.__data[model].keys())
        if preferred_region is not None and preferred_region in allowed_regions:
            region = preferred_region
        else:
            for r in allowed_regions:
                if self.__data[model][r]["tokens_remaining"] >= required_tokens:
                    region = r
                    break
        self.__data[model][region]["tokens_remaining"] -= required_tokens
        return self.__data[model][region]["meta"]
