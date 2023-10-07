from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from mypy_boto3_dynamodb.client import DynamoDBClient

from tbc.abstract_token_bucket_carousel import Model, Region, TokenBucketCarousel
from tbc.errors import InvalidModelError, InvalidRegionError

serializer = TypeSerializer()
deserializer = TypeDeserializer()


class DynamoDBTokenBucketCarousel(TokenBucketCarousel):
    def __init__(self, dynamodb_client: DynamoDBClient, table_name: str):
        self.dynamodb_client = dynamodb_client
        self.table_name = table_name
        self.models = {}

    async def list_models(self) -> set[Model]:
        models = set()
        last_evaluated_key = None

        while True:
            scan_kwargs = {
                "TableName": self.table_name,
                "ProjectionExpression": "Model",
            }

            if last_evaluated_key:
                scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

            response = self.dynamodb_client.scan(**scan_kwargs)

            if "Items" in response:
                models.update([item["Model"]["S"] for item in response["Items"]])

            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        return models

    async def list_model_regions(self, model: Model) -> set[Region]:
        response = self.dynamodb_client.query(
            TableName=self.table_name,
            KeyConditionExpression="#model = :model",
            ExpressionAttributeValues={":model": {"S": model}},
            ProjectionExpression="#region",
            ExpressionAttributeNames={"#model": "Model", "#region": "Region"},
        )
        if "Items" in response and len(response["Items"]) > 0:
            return {item["Region"]["S"] for item in response["Items"]}
        raise InvalidModelError(f"Model {model} does not exist")

    async def create_model_region(
        self,
        model: Model,
        region_name: str,
        token_allowance: int,
        token_refresh_seconds: int,
        meta: dict,
    ):
        try:
            self.dynamodb_client.put_item(
                TableName=self.table_name,
                Item={
                    "Model": {"S": model},
                    "Region": {"S": region_name},
                    "TokenAllowance": {"N": str(token_allowance)},
                    "TokenRefreshSeconds": {"N": str(token_refresh_seconds)},
                    "TokensRemaining": {"N": str(token_allowance)},
                    "LastRefresh": {"N": str(self._current_time())},
                    "Meta": serializer.serialize(meta),
                },
                ConditionExpression="attribute_not_exists(#model) AND attribute_not_exists(#region)",
                ExpressionAttributeNames={"#model": "Model", "#region": "Region"},
            )
        except self.dynamodb_client.exceptions.ConditionalCheckFailedException as err:
            raise ValueError(f"Model {model} already has region {region_name}") from err

    async def read_model_region(self, model: Model, region: Region):
        response = self.dynamodb_client.get_item(
            TableName=self.table_name,
            Key={"Model": {"S": model}, "Region": {"S": region}},
        )
        if "Item" not in response:
            raise InvalidRegionError(f"Model {model} does not have region {region}")
        return {
            "token_allowance": int(response["Item"]["TokenAllowance"]["N"]),
            "token_refresh_seconds": int(response["Item"]["TokenRefreshSeconds"]["N"]),
            "tokens_remaining": int(response["Item"]["TokensRemaining"]["N"]),
            "last_refresh": int(response["Item"]["LastRefresh"]["N"]),
            "meta": deserializer.deserialize(response["Item"]["Meta"]),
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
            self.dynamodb_client.update_item(
                TableName=self.table_name,
                Key={"Model": {"S": model}, "Region": {"S": region}},
                UpdateExpression="SET TokenAllowance = :token_allowance, TokenRefreshSeconds = :token_refresh_seconds, Meta = :meta",
                ExpressionAttributeValues={
                    ":token_allowance": {"N": str(token_allowance)},
                    ":token_refresh_seconds": {"N": str(token_refresh_seconds)},
                    ":meta": serializer.serialize(meta),
                },
                ConditionExpression="attribute_exists(#model) AND attribute_exists(#region)",
                ExpressionAttributeNames={"#model": "Model", "#region": "Region"},
            )
        except self.dynamodb_client.exceptions.ConditionalCheckFailedException as err:
            raise InvalidRegionError(
                f"Model {model} does not have region {region}"
            ) from err

    async def delete_model_region(self, model: Model, region: Region):
        try:
            self.dynamodb_client.delete_item(
                TableName=self.table_name,
                Key={"Model": {"S": model}, "Region": {"S": region}},
                ConditionExpression="attribute_exists(#model) AND attribute_exists(#region)",
                ExpressionAttributeNames={"#model": "Model", "#region": "Region"},
            )
        except self.dynamodb_client.exceptions.ConditionalCheckFailedException as err:
            raise InvalidRegionError(
                f"Model {model} does not have region {region}"
            ) from err

    async def replenish_tokens(self, model: Model, region: Region):
        # self.dynamodb_client.update_item(
        #     TableName=self.table_name,
        #     Key={"Model": {"S": model}, "Region": {"S": region}},
        #     UpdateExpression="SET TokenAllowance = TokensRemaining, #last_refresh = :now",
        #     ExpressionAttributeValues={":now": {"N": str(self.current_time())}}, # TODO: use current time in seconds
        #     ConditionExpression="attribute_not_exists(#model) AND attribute_not_exists(#region)",
        #     ExpressionAttributeNames={
        #         "#model": "Model", "#region": "Region", "#last_refresh": "LastRefresh"},
        # )
        raise NotImplementedError

    async def request_tokens(
        self,
        model: Model,
        required_tokens: int,
        fallback_models: set[Model],
        allowed_regions: set[Region],
        preferred_region: Region,
    ):
        raise NotImplementedError
