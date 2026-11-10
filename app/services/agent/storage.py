"""Durable Agent storage. SQL is authoritative; Redis is an optional hot cache.

No live DB session, API key, or handler object belongs in a checkpoint.
The same tables work on SQLite for development and PostgreSQL for deployment.
"""
import asyncio
import hashlib
import json
import time
import uuid
from contextlib import asynccontextmanager

from sqlalchemy import (MetaData, Table, Column, String, LargeBinary, Float, Text, JSON,
                        select, delete, update, and_, text)
from pgvector.sqlalchemy import Vector
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


metadata = MetaData()
records = Table(
    "agent_records", metadata,
    Column("key", String(512), primary_key=True),
    Column("value", LargeBinary, nullable=False),
    Column("expires_at", Float, nullable=False, default=0),
)
leases = Table(
    "agent_leases", metadata,
    Column("key", String(512), primary_key=True),
    Column("owner", String(36), nullable=False),
    Column("expires_at", Float, nullable=False),
)
memory_vectors = Table(
    "agent_memory_vectors", metadata,
    Column("id", String(128), primary_key=True),
    Column("namespace", String(128), nullable=False, index=True),
    Column("content", Text, nullable=False),
    Column("embedding", Vector(settings.EMBEDDING_DIM).with_variant(JSON(), "sqlite"), nullable=False),
)


def scope_key(*parts: str) -> str:
    """Length-independent, unambiguous tenant/customer/session namespace."""
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()


def tenant_key(kind, tenant_id, identifier=""):
    return f"{kind}:{scope_key(tenant_id)}:{identifier}"


class SessionBusy(Exception):
    pass


class AgentStore:
    def __init__(self, url=None, redis_url=None):
        self.engine = create_async_engine(url or settings.AGENT_DATABASE_URL, pool_pre_ping=True)
        self.redis_url = redis_url if redis_url is not None else settings.AGENT_REDIS_URL
        self._redis = None
        self._ready = False
        self._setup_lock = asyncio.Lock()

    async def setup(self):
        if self._ready:
            return
        async with self._setup_lock:
            if not self._ready:
                async with self.engine.begin() as conn:
                    if self.engine.dialect.name == "postgresql":
                        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    await conn.run_sync(metadata.create_all)
                self._ready = True

    async def redis(self):
        if self.redis_url and self._redis is None:
            from redis.asyncio import Redis
            self._redis = Redis.from_url(self.redis_url, socket_connect_timeout=1, socket_timeout=1)
        return self._redis

    async def get_bytes(self, key, *, cached=False):
        await self.setup()
        if cached and self.redis_url:
            try:
                value = await (await self.redis()).get("agent:" + key)
                if value is not None:
                    return value
            except Exception:
                pass  # SQL fallback; never substitute empty state on SQL failure.
        async with self.engine.connect() as conn:
            row = (await conn.execute(select(records).where(records.c.key == key))).mappings().first()
        if row and (not row["expires_at"] or row["expires_at"] > time.time()):
            return row["value"]
        return None

    async def put_bytes(self, key, value, ttl=0, *, cached=False):
        await self.setup()
        dialect = self.engine.dialect.name
        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert
        elif dialect == "sqlite":
            from sqlalchemy.dialects.sqlite import insert
        else:
            raise RuntimeError("Agent storage requires SQLite or PostgreSQL")
        fields = dict(key=key, value=value, expires_at=time.time() + ttl if ttl else 0)
        statement = insert(records).values(**fields)
        async with self.engine.begin() as conn:
            await conn.execute(statement.on_conflict_do_update(
                index_elements=[records.c.key], set_=fields))
        if cached and self.redis_url:
            try:
                await (await self.redis()).set("agent:" + key, value, ex=max(1, int(ttl or 86400)))
            except Exception:
                pass

    async def get(self, key, default=None, *, cached=False):
        raw = await self.get_bytes(key, cached=cached)
        return json.loads(raw) if raw else default

    async def put(self, key, value, ttl=0, *, cached=False):
        await self.put_bytes(key, json.dumps(value, ensure_ascii=False).encode(), ttl, cached=cached)

    async def scan(self, prefix, limit=None):
        await self.setup()
        async with self.engine.connect() as conn:
            statement = select(records).where(
                records.c.key.startswith(prefix, autoescape=True),
                (records.c.expires_at == 0) | (records.c.expires_at > time.time())
            ).order_by(records.c.key.desc())
            if limit is not None:
                statement = statement.limit(limit)
            rows = (await conn.execute(statement)).mappings().all()
        return rows

    async def index_memory(self, namespace, identifier, content, vector):
        await self.setup()
        async with self.engine.begin() as conn:
            await conn.execute(memory_vectors.insert().values(
                id=identifier, namespace=namespace, content=content, embedding=vector))

    async def search_memory(self, namespace, vector, limit=3):
        await self.setup()
        if self.engine.dialect.name == "postgresql":
            distance = memory_vectors.c.embedding.cosine_distance(vector)
            statement = select(memory_vectors.c.content, distance.label("distance")).where(
                memory_vectors.c.namespace == namespace, distance < .8).order_by(distance).limit(limit)
            async with self.engine.connect() as conn:
                return [row.content for row in (await conn.execute(statement))]
        import numpy as np
        async with self.engine.connect() as conn:
            rows = (await conn.execute(select(memory_vectors).where(
                memory_vectors.c.namespace == namespace).order_by(memory_vectors.c.id.desc()).limit(2000))).mappings().all()
        query_vector = np.asarray(vector)
        norm = max(float(np.linalg.norm(query_vector)), 1e-10)
        matches = []
        for row in rows:
            embedding = np.asarray(row["embedding"])
            score = float(np.dot(query_vector, embedding) / (norm * max(float(np.linalg.norm(embedding)), 1e-10)))
            if score > .2:
                matches.append((score, row["content"]))
        return [content for _, content in sorted(matches, reverse=True)[:limit]]

    async def remove(self, key):
        await self.setup()
        async with self.engine.begin() as conn:
            await conn.execute(delete(records).where(records.c.key == key))
        if self.redis_url:
            try:
                await (await self.redis()).delete("agent:" + key)
            except Exception:
                pass

    async def reserve(self, key, value, ttl=0):
        """Atomic insert: used for write-operation idempotency across workers."""
        await self.setup()
        try:
            async with self.engine.begin() as conn:
                await conn.execute(records.insert().values(
                    key=key, value=json.dumps(value).encode(),
                    expires_at=time.time() + ttl if ttl else 0))
            return True
        except IntegrityError:
            return False

    async def update_json(self, key, mutate, default=None, ttl=0):
        """Short, serialized read-modify-write across all application workers."""
        for attempt in range(20):
            try:
                async with self.lock("record:" + key, seconds=10):
                    value = mutate(await self.get(key, default))
                    await self.put(key, value, ttl=ttl)
                    return value
            except SessionBusy:
                if attempt == 19:
                    raise
                await asyncio.sleep(.01)

    @asynccontextmanager
    async def lock(self, key, seconds=None):
        """Cross-process lease. Runtime timeout is strictly shorter than the lease."""
        await self.setup()
        owner = str(uuid.uuid4())
        expires = time.time() + (seconds or settings.AGENT_TIMEOUT_SECONDS + 30)
        try:
            async with self.engine.begin() as conn:
                reclaimed = await conn.execute(update(leases).where(
                    leases.c.key == key, leases.c.expires_at < time.time()
                ).values(owner=owner, expires_at=expires))
                if not reclaimed.rowcount:
                    await conn.execute(leases.insert().values(key=key, owner=owner, expires_at=expires))
        except IntegrityError as exc:
            raise SessionBusy("该会话正在处理上一条请求，请稍后重试。") from exc
        try:
            yield
        finally:
            async with self.engine.begin() as conn:
                await conn.execute(delete(leases).where(and_(leases.c.key == key, leases.c.owner == owner)))


agent_store = AgentStore()
