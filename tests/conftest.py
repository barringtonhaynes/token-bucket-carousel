import os
from unittest.mock import patch

import boto3
import pytest
from moto import mock_dynamodb

from tbc import (
    DynamoDBTokenBucketCarousel,
    InMemoryTokenBucketCarousel,
    TokenBucketCarousel,
)


@pytest.fixture(scope="function")
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture(scope="function")
def dynamodb_client(aws_credentials):
    with mock_dynamodb():
        conn = boto3.client("dynamodb")
        yield conn


@pytest.fixture
def in_memory_token_bucket():
    return InMemoryTokenBucketCarousel()


@pytest.fixture
def dynamodb_token_bucket(dynamodb_client):
    table_name = "token-table"

    dynamodb_client.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "Model", "KeyType": "HASH"},
            {"AttributeName": "Region", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "Model", "AttributeType": "S"},
            {"AttributeName": "Region", "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )
    dynamodb_client.get_waiter("table_exists").wait(TableName=table_name)

    return DynamoDBTokenBucketCarousel(
        dynamodb_client=dynamodb_client, table_name=table_name
    )


# redis_token_bucket_carousel = RedisTokenBucketCarousel({"url": "redis://localhost:6379/0"})


@pytest.fixture(
    params=[
        "in_memory_token_bucket",
        "dynamodb_token_bucket",
        # 'redis_token_bucket',
    ]
)
def token_bucket(request):
    """Yield an instance of token bucket based on the parameterized fixture."""
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
async def populated_token_bucket(token_bucket: TokenBucketCarousel):
    with patch.object(token_bucket, "_current_time", return_value=12345):
        await token_bucket.create_model_region(
            "MODEL-1", "uk", 1, 1, {"model": "MODEL-1", "region": "uk"}
        )
        await token_bucket.create_model_region(
            "MODEL-1", "us", 5, 1, {"model": "MODEL-1", "region": "us"}
        )
        await token_bucket.create_model_region(
            "MODEL-2", "uk", 10, 1, {"model": "MODEL-2", "region": "uk"}
        )
        await token_bucket.create_model_region(
            "MODEL-2", "us", 20, 1, {"model": "MODEL-2", "region": "us"}
        )
    return token_bucket
