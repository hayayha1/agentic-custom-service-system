"""LangGraph BaseCheckpointSaver with SQL audit history and Redis hot snapshots."""
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple, WRITES_IDX_MAP

from app.services.agent.storage import agent_store


class DurableCheckpointSaver(BaseCheckpointSaver):
    def __init__(self, store=agent_store):
        super().__init__()
        self.store = store

    @staticmethod
    def _prefix(config):
        c = config["configurable"]
        return f"checkpoint:{c['thread_id']}:{c.get('checkpoint_ns', '')}:"

    def _dump(self, value):
        kind, data = self.serde.dumps_typed(value)
        return kind.encode() + b"\n" + data

    def _load(self, data):
        kind, value = data.split(b"\n", 1)
        return self.serde.loads_typed((kind.decode(), value))

    async def aget_tuple(self, config):
        prefix = self._prefix(config)
        checkpoint_id = config["configurable"].get("checkpoint_id")
        if not checkpoint_id:
            rows = await self.store.scan(prefix, limit=1)
            if not rows:
                return None
            checkpoint_id = rows[0]["key"][len(prefix):]
        raw = await self.store.get_bytes(prefix + checkpoint_id, cached=True)
        if not raw:
            return None
        record = self._load(raw)
        writes = await self.store.scan(f"writes:{prefix}{checkpoint_id}:")
        pending = [self._load(row["value"]) for row in writes]
        return CheckpointTuple(record["config"], record["checkpoint"], record["metadata"],
                               record["parent_config"], pending)

    async def aput(self, config, checkpoint, metadata, new_versions):
        c = config["configurable"]
        next_config = {"configurable": {"thread_id": c["thread_id"],
                       "checkpoint_ns": c.get("checkpoint_ns", ""), "checkpoint_id": checkpoint["id"]}}
        parent = {"configurable": {"thread_id": c["thread_id"], "checkpoint_ns": c.get("checkpoint_ns", ""),
                                  "checkpoint_id": c["checkpoint_id"]}} if c.get("checkpoint_id") else None
        # LangGraph configs also contain live runtime dependencies and callbacks.
        # Only stable checkpoint coordinates may be persisted as parent config.
        checkpoint = {**checkpoint, "channel_values": dict(checkpoint["channel_values"])}
        record = dict(config=next_config, checkpoint=checkpoint, metadata=dict(metadata), parent_config=parent)
        await self.store.put_bytes(self._prefix(config) + checkpoint["id"], self._dump(record), cached=True)
        return next_config

    async def aput_writes(self, config, writes, task_id, task_path=""):
        prefix = f"writes:{self._prefix(config)}{config['configurable']['checkpoint_id']}:"
        for index, (channel, value) in enumerate(writes):
            idx = WRITES_IDX_MAP.get(channel, index)
            key = f"{prefix}{task_id}:{idx:+08d}"
            # Normal writes are first-write-wins; special interrupt/error channels replace.
            if idx >= 0 and await self.store.get_bytes(key) is not None:
                continue
            await self.store.put_bytes(key, self._dump((task_id, channel, value)))

    async def alist(self, config, *, filter=None, before=None, limit=None):
        if config is None:
            raise ValueError("A tenant-scoped thread configuration is required")
        count = 0
        for row in await self.store.scan(self._prefix(config)):
            record = self._load(row["value"])
            cp_id = record["checkpoint"]["id"]
            if before and cp_id >= before["configurable"]["checkpoint_id"]:
                continue
            if filter and any(record["metadata"].get(k) != v for k, v in filter.items()):
                continue
            if limit is not None and count >= limit:
                break
            yield await self.aget_tuple(record["config"])
            count += 1

    async def adelete_thread(self, thread_id):
        for prefix in (f"checkpoint:{thread_id}:", f"writes:checkpoint:{thread_id}:"):
            for row in await self.store.scan(prefix):
                await self.store.remove(row["key"])
