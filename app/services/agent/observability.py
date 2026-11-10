"""Redacted decision/event traces, bounded metrics, optional OTLP export.

Record decisions and observations, never private chain-of-thought reasoning.
"""
import json
import time
import uuid
from collections import Counter, deque
from contextlib import nullcontext

from app.services.agent.safety import redact
from app.services.agent.storage import agent_store, tenant_key


class AgentTelemetry:
    def __init__(self, store=agent_store):
        self.store = store
        self.counts = Counter()
        self.latencies = deque(maxlen=1000)
        self.latency_count = 0
        self.latency_sum = 0.0
        self.alerts = deque(maxlen=100)
        self.duration_buckets = Counter()
        self.tracer = None

    def configure(self):
        from app.core.config import settings
        if settings.AGENT_OTLP_ENDPOINT and self.tracer is None:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            provider = TracerProvider()
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.AGENT_OTLP_ENDPOINT)))
            self.tracer = provider.get_tracer("zhishu.agent")
            self.provider = provider

    def request_span(self):
        return self.tracer.start_as_current_span("agent.request") if self.tracer else nullcontext()

    async def event(self, state, kind, data):
        self.counts[kind] += 1
        if kind == "tool":
            observation = data.get("observation", {})
            if observation.get("status") != "success":
                self.counts["tool_failure"] += 1
            if observation.get("data", {}).get("reason") in {"circuit_open", "rate_limit"}:
                self.counts[observation["data"]["reason"]] += 1
        event = redact({"kind": kind, "data": data, "time": time.time()})
        events = state.get("events", []) + [event]
        if self.tracer:
            with self.tracer.start_as_current_span("agent." + kind) as span:
                span.set_attribute("agent.trace_id", state["trace_id"])
                span.set_attribute("agent.event", json.dumps(event, ensure_ascii=False))
        return events[-64:]

    async def finish(self, identity, result, elapsed):
        self.latencies.append(elapsed)
        self.latency_count += 1
        self.latency_sum += elapsed
        for boundary in [.1, .25, .5, 1, 2, 5, 10, 30, 60, 120, 300]:
            if elapsed <= boundary:
                self.duration_buckets[boundary] += 1
        self.counts["requests"] += 1
        status = result.get("status", "unknown")
        self.counts["status_" + status] += 1
        self.counts["tokens"] += result.get("request_tokens", result.get("tokens", 0))
        trace = redact({"trace_id": result["trace_id"], "tenant_id": identity.tenant_id,
                        "customer_id": identity.customer_id, "session_id": identity.session_id,
                        "query": result.get("raw_query"), "plan": result.get("plan"),
                        "events": result.get("events", []), "status": status,
                        "tokens": result.get("tokens", 0), "elapsed_seconds": elapsed,
                        "iterations": result.get("iterations", 0), "content": result.get("final_content")})
        if self.tracer:
            from opentelemetry import trace as otel_trace
            span = otel_trace.get_current_span()
            span.set_attribute("agent.trace_id", result["trace_id"])
            span.set_attribute("agent.status", status)
            trace["otel_trace_id"] = format(span.get_span_context().trace_id, "032x")
        await self.store.put(tenant_key("trace", identity.tenant_id, result["trace_id"]), trace)
        await self.store.put(tenant_key("request_trace", identity.tenant_id, str(uuid.uuid4())), trace)
        if status in {"failed", "timeout", "iteration_limit", "blocked", "human"} or result.get("top_score", 1) < 0.4:
            await self.store.put(tenant_key("badtrace", identity.tenant_id, result["trace_id"]), trace)
            self.alerts.append({"trace_id": result["trace_id"], "status": status})

    def prometheus(self):
        lines = ["# TYPE agent_events_total counter"]
        for kind, count in sorted(self.counts.items()):
            lines.append(f'agent_events_total{{event="{kind}"}} {count}')
        values = sorted(self.latencies)
        p95 = values[min(len(values) - 1, int(len(values) * .95))] if values else 0
        lines += ["# TYPE agent_response_p95_seconds gauge", f"agent_response_p95_seconds {p95}",
                  "# TYPE agent_request_duration_seconds histogram",
                  f"agent_request_duration_seconds_count {self.latency_count}",
                  f"agent_request_duration_seconds_sum {self.latency_sum}"]
        for boundary in [.1, .25, .5, 1, 2, 5, 10, 30, 60, 120, 300]:
            lines.append(f'agent_request_duration_seconds_bucket{{le="{boundary}"}} {self.duration_buckets[boundary]}')
        lines.append(f'agent_request_duration_seconds_bucket{{le="+Inf"}} {self.latency_count}')
        return "\n".join(lines) + "\n"


agent_telemetry = AgentTelemetry()
