import pytest

from tbc.abstract_token_bucket_carousel import TokenBucketCarousel
from tbc.errors import InvalidModelError, InvalidRegionError


async def test_list_models(populated_token_bucket: TokenBucketCarousel):
    models = await populated_token_bucket.list_models()
    print("modelsy", models)
    assert models == {"MODEL-1", "MODEL-2"}, "Models not listed"


async def test_list_100_models(token_bucket: TokenBucketCarousel):
    for i in range(100):
        for j in range(2):
            await token_bucket.create_model_region(
                f"MODEL-{i}",
                f"uk-{j}",
                1,
                1,
                {"model": f"MODEL-{i}", "region": f"uk-{j}"},
            )
    models = await token_bucket.list_models()
    assert len(models) == 100, "Models not listed"


async def test_list_model_does_not_exist(populated_token_bucket: TokenBucketCarousel):
    with pytest.raises(InvalidModelError, match="Model MODEL-3 does not exist"):
        await populated_token_bucket.list_model_regions("MODEL-3")


@pytest.mark.parametrize(
    ["model", "x_regions"], [("MODEL-1", {"uk", "us"}), ("MODEL-2", {"uk", "us"})]
)
async def test_list_model_regions(
    populated_token_bucket: TokenBucketCarousel, model, x_regions
):
    regions = await populated_token_bucket.list_model_regions(model)
    assert regions == x_regions, "Regions not listed"


async def test_create_model_region(populated_token_bucket: TokenBucketCarousel):
    await populated_token_bucket.create_model_region(
        "MODEL-3", "uk", 1, 1, {"model": "MODEL-3", "region": "uk"}
    )
    regions = await populated_token_bucket.list_model_regions("MODEL-3")
    assert "uk" in regions, "Region not created"


async def test_create_model_region_already_exists(
    populated_token_bucket: TokenBucketCarousel,
):
    with pytest.raises(ValueError, match="Model MODEL-1 already has region uk"):
        await populated_token_bucket.create_model_region(
            "MODEL-1", "uk", 1, 1, {"model": "MODEL-1", "region": "uk"}
        )


async def test_read_model_region(populated_token_bucket: TokenBucketCarousel):
    region = await populated_token_bucket.read_model_region("MODEL-1", "uk")
    assert region == {
        "token_allowance": 1,
        "token_refresh_seconds": 1,
        "meta": {"model": "MODEL-1", "region": "uk"},
        "tokens_remaining": 1,
        "last_refresh": 12345,
    }, "Region not read"


async def test_read_model_region_does_not_exist(
    populated_token_bucket: TokenBucketCarousel,
):
    with pytest.raises(
        InvalidRegionError, match="Model MODEL-1 does not have region fr"
    ):
        await populated_token_bucket.read_model_region("MODEL-1", "fr")


async def test_update_model_region(populated_token_bucket: TokenBucketCarousel):
    await populated_token_bucket.update_model_region(
        "MODEL-1", "uk", 2, 2, {"model": "MODEL-1", "region": "uk"}
    )
    region = await populated_token_bucket.read_model_region("MODEL-1", "uk")
    assert region == {
        "token_allowance": 2,
        "token_refresh_seconds": 2,
        "meta": {"model": "MODEL-1", "region": "uk"},
        "tokens_remaining": 1,
        "last_refresh": 12345,
    }, "Region not updated"


async def test_update_model_region_does_not_exist(
    populated_token_bucket: TokenBucketCarousel,
):
    with pytest.raises(
        InvalidRegionError, match="Model MODEL-1 does not have region fr"
    ):
        await populated_token_bucket.update_model_region(
            "MODEL-1", "fr", 2, 2, {"model": "MODEL-1", "region": "fr"}
        )


async def test_delete_model_region(populated_token_bucket: TokenBucketCarousel):
    await populated_token_bucket.delete_model_region("MODEL-1", "uk")
    regions = await populated_token_bucket.list_model_regions("MODEL-1")
    assert "uk" not in regions, "Region not deleted"


async def test_delete_model_region_does_not_exist(
    populated_token_bucket: TokenBucketCarousel,
):
    with pytest.raises(
        InvalidRegionError, match="Model MODEL-1 does not have region fr"
    ):
        await populated_token_bucket.delete_model_region("MODEL-1", "fr")
