"""Shared MongoDB helpers used across the Python agent stack."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(override=True)


def _clean_env_value(value: str | None) -> str | None:
    """Strip quoting artifacts from env values loaded via Docker or `.env`."""

    if value is None:
        return None
    cleaned = value.strip().strip("\"'")
    return cleaned or None


def _looks_like_placeholder_mongo_uri(uri: str | None) -> bool:
    """Detect obviously non-production Mongo URIs copied from templates/docs."""

    candidate = _clean_env_value(uri)
    if not candidate:
        return False

    lowered = candidate.lower()
    return any(
        token in lowered
        for token in (
            "cluster.mongodb.net",
            "username:password",
            "user:password",
            "<username>",
            "<password>",
            "example.mongodb.net",
        )
    )


class MongoDBTools:
    """Small async MongoDB toolkit shared by repositories and agents."""

    _mongo_client: AsyncIOMotorClient | None = None

    @classmethod
    def _mongo_uri(cls) -> str | None:
        return _clean_env_value(os.getenv("MONGO_URI"))

    @classmethod
    def get_mongo_client(cls) -> AsyncIOMotorClient:
        if cls._mongo_client is None:
            mongo_uri = cls._mongo_uri()
            if not mongo_uri:
                raise RuntimeError("MONGO_URI is not configured.")
            if _looks_like_placeholder_mongo_uri(mongo_uri):
                raise RuntimeError(
                    "MONGO_URI đang là giá trị mẫu/placeholder, chưa phải Mongo URI thật. "
                    "Hãy cập nhật infra/.env.ai hoặc biến môi trường runtime bằng connection string Mongo hợp lệ."
                )
            cls._mongo_client = AsyncIOMotorClient(mongo_uri)
        return cls._mongo_client

    def _on_mongo_event(self, message: str) -> None:
        """Hook for subclasses to bridge Mongo events into their logger."""

        _ = message

    def _collection(self, database_name: str, collection_name: str):
        client = self.get_mongo_client()
        return client[database_name][collection_name]

    async def get_data(
        self,
        database_name: str,
        collection_name: str,
        query: dict,
        limit: int = 10,
    ) -> list[dict]:
        self._on_mongo_event(
            f"mongo:get_data:start db={database_name} collection={collection_name} "
            f"limit={limit} query_keys={len(query)}"
        )
        collection = self._collection(database_name, collection_name)
        result = await collection.find(query).to_list(length=limit)
        self._on_mongo_event(
            f"mongo:get_data:done db={database_name} collection={collection_name} "
            f"result={len(result)}"
        )
        return result

    async def get_one(
        self,
        database_name: str,
        collection_name: str,
        query: dict,
    ) -> dict | None:
        self._on_mongo_event(
            f"mongo:get_one:start db={database_name} collection={collection_name} "
            f"query_keys={len(query)}"
        )
        collection = self._collection(database_name, collection_name)
        result = await collection.find_one(query)
        self._on_mongo_event(
            f"mongo:get_one:done db={database_name} collection={collection_name} "
            f"found={result is not None}"
        )
        return result

    async def insert_data(
        self,
        database_name: str,
        collection_name: str,
        documents: list[dict],
    ) -> None:
        if not documents:
            self._on_mongo_event(
                f"mongo:insert_data:skip_empty db={database_name} "
                f"collection={collection_name}"
            )
            return

        self._on_mongo_event(
            f"mongo:insert_data:start db={database_name} collection={collection_name} "
            f"documents={len(documents)}"
        )
        collection = self._collection(database_name, collection_name)
        await collection.insert_many(documents)
        self._on_mongo_event(
            f"mongo:insert_data:done db={database_name} collection={collection_name} "
            f"documents={len(documents)}"
        )

    async def insert_one(
        self,
        database_name: str,
        collection_name: str,
        document: dict,
    ):
        self._on_mongo_event(
            f"mongo:insert_one:start db={database_name} collection={collection_name} "
            f"keys={len(document)}"
        )
        collection = self._collection(database_name, collection_name)
        result = await collection.insert_one(document)
        self._on_mongo_event(
            f"mongo:insert_one:done db={database_name} collection={collection_name}"
        )
        return result.inserted_id

    async def update_one(
        self,
        database_name: str,
        collection_name: str,
        query: dict,
        update: dict,
        upsert: bool = False,
    ) -> int:
        self._on_mongo_event(
            f"mongo:update_one:start db={database_name} collection={collection_name} "
            f"query_keys={len(query)} update_keys={len(update)} upsert={upsert}"
        )
        collection = self._collection(database_name, collection_name)
        result = await collection.update_one(query, update, upsert=upsert)
        self._on_mongo_event(
            f"mongo:update_one:done db={database_name} collection={collection_name} "
            f"matched={result.matched_count} modified={result.modified_count} "
            f"upserted={result.upserted_id is not None}"
        )
        return result.modified_count

    async def upsert_one(
        self,
        database_name: str,
        collection_name: str,
        query: dict,
        payload: dict,
    ) -> int:
        return await self.update_one(
            database_name,
            collection_name,
            query,
            {"$set": payload},
            upsert=True,
        )
