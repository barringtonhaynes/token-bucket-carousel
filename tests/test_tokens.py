import pytest

from tbc.abstract_token_bucket_carousel import TokenBucketCarousel
from tbc.errors import InvalidRegionError


def test_replenish_tokens(populated_token_bucket: TokenBucketCarousel):
    populated_token_bucket.replenish_tokens("MODEL-1", "uk")
    region = populated_token_bucket.read_model_region("MODEL-1", "uk")
    assert region["tokens_remaining"] == region["token_allowance"]


def test_replenish_tokens_unknown_region(populated_token_bucket: TokenBucketCarousel):
    with pytest.raises(
        InvalidRegionError, match="Model MODEL-1 does not have region fr"
    ):
        populated_token_bucket.replenish_tokens("MODEL-1", "fr")


async def test_request_1_token(populated_token_bucket: TokenBucketCarousel):
    meta = await populated_token_bucket.request_tokens("MODEL-1", 1)
    region = populated_token_bucket.read_model_region(meta["model"], meta["region"])
    assert region["tokens_remaining"] == region["token_allowance"] - 1
