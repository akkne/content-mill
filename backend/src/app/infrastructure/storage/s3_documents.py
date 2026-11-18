import os
from functools import cached_property

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.domain.knowledge import DocumentStorageError


class S3DocumentStore:
    def __init__(self) -> None:
        self.bucket = os.environ.get("S3_BUCKET", "content-mill")

    @cached_property
    def client(self):
        return boto3.client(
            "s3",
            endpoint_url=os.environ.get("S3_ENDPOINT_URL"),
            region_name=os.environ.get("S3_REGION", "us-east-1"),
            aws_access_key_id=os.environ.get("S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("S3_SECRET_ACCESS_KEY"),
            config=Config(s3={"addressing_style": "path"}),
        )

    def put(self, key: str, content: bytes, content_type: str) -> None:
        try:
            self.client.put_object(
                Bucket=self.bucket, Key=key, Body=content, ContentType=content_type
            )
        except (BotoCoreError, ClientError) as error:
            raise DocumentStorageError("Хранилище документов недоступно") from error

    def get(self, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except (BotoCoreError, ClientError) as error:
            raise DocumentStorageError("Документ недоступен") from error

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError) as error:
            raise DocumentStorageError("Не удалось очистить объект") from error
