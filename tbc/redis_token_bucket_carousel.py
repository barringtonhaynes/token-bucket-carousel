import json

from redis import Redis
from redis.exceptions import ResponseError

from tbc.abstract_token_bucket_carousel import Model, Region, TokenBucketCarousel
from tbc.errors import InvalidModelError, InvalidRegionError

CREATE_LUA_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 1 then
    return redis.error_reply('Key already exists')
else
    redis.call('HSET', KEYS[1], 'token_allowance', ARGV[1], 'token_refresh_seconds', ARGV[2], 'meta', ARGV[3], 'tokens_remaining', ARGV[4], 'last_refresh', ARGV[5])
    return redis.status_reply('OK')
end
"""

UPDATE_LUA_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 0 then
    return redis.error_reply('Key does not exist')
else
    redis.call('HSET', KEYS[1], 'token_allowance', ARGV[1], 'token_refresh_seconds', ARGV[2], 'meta', ARGV[3])
    return redis.status_reply('OK')
end
"""


class RedisTokenBucketCarousel(TokenBucketCarousel):
    def __init__(self, redis_client: Redis, namespace: str = "tbc"):
        self.redis_client = redis_client
        self.namespace = namespace
        self.models = {}

    def _key(self, model: Model, region: Region = None) -> str:
        if region is None:
            return f"{self.namespace}:{model}"
        return f"{self.namespace}:{model}:{region}"

    async def list_models(self) -> set[Model]:
        keys = self.redis_client.keys(self._key("*"))
        return {key.split(":")[-2] for key in keys}

    async def list_model_regions(self, model: Model) -> set[Region]:
        keys = self.redis_client.keys(self._key(model, "*"))
        if keys:
            return {key.split(":")[-1] for key in keys}
        raise InvalidModelError(f"Model {model} does not exist")

    async def create_model_region(
        self,
        model: Model,
        region: Region,
        token_allowance: int,
        token_refresh_seconds: int,
        meta: dict,
    ):
        try:
            self.redis_client.eval(
                CREATE_LUA_SCRIPT,
                1,
                self._key(model, region),
                token_allowance,
                token_refresh_seconds,
                json.dumps(meta),
                token_allowance,
                self._current_time(),
            )
        except ResponseError as err:
            if "Key already exists" in str(err):
                raise ValueError(f"Model {model} already has region {region}") from err
            raise

    async def read_model_region(self, model: Model, region: Region):
        data = self.redis_client.hgetall(self._key(model, region))
        if not data:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        return {
            "token_allowance": int(data["token_allowance"]),
            "token_refresh_seconds": int(data["token_refresh_seconds"]),
            "meta": json.loads(data["meta"]),
            "tokens_remaining": int(data["tokens_remaining"]),
            "last_refresh": int(data["last_refresh"]),
        }

    async def update_model_region(
        self,
        model: Model,
        region: Region,
        token_allowance: int,
        token_refresh_seconds: int,
        meta: dict,
    ):
        try:
            self.redis_client.eval(
                UPDATE_LUA_SCRIPT,
                1,
                self._key(model, region),
                token_allowance,
                token_refresh_seconds,
                json.dumps(meta),
            )
        except ResponseError as err:
            if "Key does not exist" in str(err):
                raise InvalidRegionError(
                    f"Model {model} does not have region {region}"
                ) from err
            raise

    async def delete_model_region(self, model: Model, region: Region):
        key_count = self.redis_client.delete(self._key(model, region))
        if key_count == 0:
            raise InvalidRegionError(f"Model {model} does not have region {region}")

    async def replenish_tokens(self, model: Model, region: Region):
        raise NotImplementedError

    async def request_tokens(
        self,
        model: Model,
        required_tokens: int,
        fallback_models: set[Model],
        allowed_regions: set[Region],
    ):
        raise NotImplementedError
