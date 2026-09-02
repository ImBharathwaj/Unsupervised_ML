#!/usr/bin/env python3
"""Serve lightweight synthetic streaming datasets over HTTP."""

from __future__ import annotations

import json
import os
import random
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from itertools import cycle
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


COUNTRIES = ["IN", "US", "SG", "AE", "GB"]
CHANNELS = ["WEB", "MOBILE_APP", "BRANCH", "CALL_CENTER", "PARTNER", "API"]
TRANSACTION_TYPES = ["CREDIT", "DEBIT", "TRANSFER", "ATM_WITHDRAWAL", "CARD_PAYMENT", "UPI"]
BEHAVIOR_EVENTS = [
    "LOGIN",
    "LOAN_PAGE_VIEW",
    "LOAN_APPLICATION_START",
    "LOAN_APPLICATION_SUBMIT",
    "INSURANCE_QUOTE",
    "PROFILE_UPDATE",
]
MARKETING_EVENTS = [
    "CAMPAIGN_SENT",
    "CAMPAIGN_DELIVERED",
    "CAMPAIGN_OPENED",
    "CAMPAIGN_CLICKED",
    "CONVERSION",
]
CREDIT_EVENTS = [
    "CREDIT_SCORE_UPDATED",
    "NEW_CREDIT_ACCOUNT",
    "CREDIT_ENQUIRY",
    "DELINQUENCY_REPORTED",
]
DEFAULT_HOST = os.getenv("STREAMING_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("STREAMING_PORT", "8882"))
DEFAULT_RATE = float(os.getenv("STREAMING_RATE", "1"))
DEFAULT_SCHEMA = os.getenv("STREAMING_SCHEMA", "schema.json")


def load_schema(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class StreamingGenerator:
    def __init__(self, schema: dict[str, Any], seed: int = 42) -> None:
        self.schema = schema
        self.reference_values = schema.get("reference_values", {})
        self.random = random.Random(seed)
        self.counters = {name: 0 for name in schema["datasets"]["streaming"]}

    def dataset_names(self) -> list[str]:
        return list(self.schema["datasets"]["streaming"])

    def dataset_info(self) -> list[dict[str, str]]:
        info = []
        for dataset_name, config in self.schema["datasets"]["streaming"].items():
            info.append(
                {
                    "dataset": dataset_name,
                    "path": f"/events/{dataset_name}",
                    "topic": config["kafka_topic"],
                    "description": config["description"],
                }
            )
        return info

    def generate_envelope(self, dataset_name: str) -> dict[str, Any]:
        datasets = self.schema["datasets"]["streaming"]
        if dataset_name not in datasets:
            raise KeyError(f"Unknown streaming dataset: {dataset_name}")

        index = self.counters[dataset_name]
        self.counters[dataset_name] += 1
        payload = self.generate_event(dataset_name, index)
        return {
            "dataset": dataset_name,
            "topic": datasets[dataset_name]["kafka_topic"],
            "emitted_at": datetime.now().replace(microsecond=0).isoformat(),
            "sequence": index,
            "payload": payload,
        }

    def generate_event(self, dataset_name: str, index: int) -> dict[str, Any]:
        datasets = self.schema["datasets"]["streaming"]
        event_schema = datasets[dataset_name]["schema"]
        event = {
            field_name: self._generate_value(dataset_name, field_name, field_type, index)
            for field_name, field_type in event_schema.items()
        }
        self._validate_event(event_schema, event)
        return event

    def _generate_value(self, dataset_name: str, field_name: str, field_type: str, index: int) -> Any:
        base_type, nullable = self._normalize_type(field_type)
        if nullable and self.random.random() < 0.2:
            return None

        if field_name.endswith("_id") or field_name in {"session_id", "device_id"}:
            return self._generate_identifier(field_name, index)
        if field_name in {"event_time"} or base_type == "timestamp":
            return self._generate_timestamp()
        if base_type == "integer":
            return self._generate_integer(field_name)
        if base_type == "decimal":
            return self._generate_decimal(field_name)
        if base_type == "object":
            return self._generate_object(dataset_name, field_name)
        return self._generate_string(dataset_name, field_name, index)

    @staticmethod
    def _normalize_type(field_type: str) -> tuple[str, bool]:
        parts = field_type.split("|")
        nullable = "null" in parts
        base_type = next(part for part in parts if part != "null")
        return base_type, nullable

    def _generate_identifier(self, field_name: str, index: int) -> str:
        prefix = field_name.removesuffix("_id").upper() or "ID"
        token = uuid.UUID(int=self.random.getrandbits(128)).hex[:10]
        return f"{prefix}_{index:06d}_{token}"

    def _generate_timestamp(self) -> str:
        now = datetime.now()
        stamp = now - timedelta(seconds=self.random.randint(0, 300))
        return stamp.replace(microsecond=0).isoformat()

    def _generate_integer(self, field_name: str) -> int:
        if "score" in field_name:
            return self.random.randint(300, 900)
        if "change" in field_name:
            return self.random.randint(-80, 80)
        if "count" in field_name:
            return self.random.randint(0, 10)
        return self.random.randint(0, 100)

    def _generate_decimal(self, field_name: str) -> float:
        if "balance" in field_name:
            value = self.random.uniform(1000, 1000000)
        elif "premium" in field_name:
            value = self.random.uniform(1000, 100000)
        else:
            value = self.random.uniform(100, 500000)
        return float(Decimal(str(value)).quantize(Decimal("0.01")))

    def _generate_object(self, dataset_name: str, field_name: str) -> dict[str, Any]:
        if field_name == "changed_fields":
            return {
                "field": self.random.choice(["email", "phone", "address_line_1", "customer_segment"]),
                "old_value": self.random.choice(["old@example.com", "9999999999", "MASS"]),
                "new_value": self.random.choice(["new@example.com", "8888888888", "AFFLUENT"]),
            }
        return {
            "dataset": dataset_name,
            "trace_id": uuid.UUID(int=self.random.getrandbits(128)).hex,
            "source": self.random.choice(["mobile", "web", "crm", "partner"]),
            "priority": self.random.choice(["low", "medium", "high"]),
        }

    def _generate_string(self, dataset_name: str, field_name: str, index: int) -> str:
        if field_name == "customer_id":
            return self._generate_identifier(field_name, self.random.randint(1, 5000))
        if field_name == "account_id":
            return self._generate_identifier(field_name, self.random.randint(1, 2500))
        if field_name == "transaction_type":
            return self.random.choice(self.reference_values.get("transaction_types", TRANSACTION_TYPES))
        if field_name == "currency":
            return self.random.choice(["INR", "USD", "SGD", "AED"])
        if field_name == "merchant_name":
            return self.random.choice(["Amazon", "Walmart", "Uber", "Swiggy", "Shell"])
        if field_name == "merchant_category":
            return self.random.choice(["RETAIL", "TRAVEL", "DINING", "FUEL", "GROCERY"])
        if field_name == "channel":
            return self.random.choice(self.reference_values.get("customer_channels", CHANNELS))
        if field_name == "location":
            return self.random.choice(["Bengaluru", "Mumbai", "Dubai", "Singapore", "London"])
        if field_name == "page":
            return self.random.choice(["/home", "/loans", "/insurance", "/offers", "/profile"])
        if field_name == "product":
            return self.random.choice(["LOAN", "INSURANCE", "CREDIT_CARD", "SAVINGS"])
        if field_name == "source":
            return self.random.choice(["GOOGLE", "META", "CRM", "AFFILIATE"])
        if field_name == "device_type":
            return self.random.choice(["ANDROID", "IOS", "WEB"])
        if field_name == "ip_country":
            return self.random.choice(COUNTRIES)
        if field_name == "event_type":
            return self._event_type(dataset_name)
        if field_name == "bureau":
            return self.random.choice(self.reference_values.get("credit_bureaus", ["CIBIL"]))
        if field_name == "loan_type":
            return self.random.choice(self.reference_values.get("loan_types", ["PERSONAL_LOAN"]))
        if field_name == "policy_type":
            return self.random.choice(self.reference_values.get("insurance_types", ["LIFE"]))
        if field_name == "status":
            return self.random.choice(["STARTED", "SUBMITTED", "APPROVED", "DECLINED", "ACTIVE"])
        if field_name == "operation":
            return self.random.choice(["INSERT", "UPDATE", "DELETE"])
        if field_name == "source_system":
            return self.random.choice(["CRM", "LOS", "CBS", "MOBILE_APP"])
        return f"{field_name}_{index:06d}"

    def _event_type(self, dataset_name: str) -> str:
        if dataset_name == "customer_behavior_events":
            return self.random.choice(self.reference_values.get("behavior_events", BEHAVIOR_EVENTS))
        if dataset_name == "marketing_events":
            return self.random.choice(self.reference_values.get("marketing_events", MARKETING_EVENTS))
        if dataset_name == "credit_events":
            return self.random.choice(self.reference_values.get("credit_event_types", CREDIT_EVENTS))
        return self.random.choice(["CREATED", "UPDATED", "SUBMITTED", "VIEWED"])

    @staticmethod
    def _validate_event(event_schema: dict[str, str], event: dict[str, Any]) -> None:
        for field_name, field_type in event_schema.items():
            _, nullable = StreamingGenerator._normalize_type(field_type)
            if event[field_name] is None and not nullable:
                raise ValueError(f"Field {field_name} is null but declared as {field_type}")


class StreamingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address: tuple[str, int], handler_class: type[BaseHTTPRequestHandler], app: "StreamingApp"):
        super().__init__(server_address, handler_class)
        self.app = app


class StreamingHandler(BaseHTTPRequestHandler):
    server: StreamingHTTPServer
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._write_json({"status": "ok"})
            return
        if parsed.path == "/datasets":
            self._write_json({"datasets": self.server.app.generator.dataset_info()})
            return
        if parsed.path == "/events":
            self._stream_events(dataset_name=None, query=parse_qs(parsed.query))
            return
        if parsed.path.startswith("/events/"):
            dataset_name = parsed.path.removeprefix("/events/").strip("/")
            self._stream_events(dataset_name=dataset_name, query=parse_qs(parsed.query))
            return
        self._write_json(
            {
                "error": "Not found",
                "available_paths": ["/health", "/datasets", "/events"]
                + [item["path"] for item in self.server.app.generator.dataset_info()],
            },
            status=HTTPStatus.NOT_FOUND,
        )

    def _stream_events(self, dataset_name: str | None, query: dict[str, list[str]]) -> None:
        dataset_names = self.server.app.generator.dataset_names()
        if dataset_name is not None and dataset_name not in dataset_names:
            self._write_json(
                {
                    "error": f"Unknown dataset '{dataset_name}'",
                    "available_datasets": dataset_names,
                },
                status=HTTPStatus.NOT_FOUND,
            )
            return

        limit = self._query_int(query, "limit", default=0)
        rate = self._query_float(query, "rate", default=self.server.app.rate)
        interval = 0.0 if rate <= 0 else 1.0 / rate
        names = cycle(dataset_names) if dataset_name is None else cycle([dataset_name])

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        emitted = 0
        try:
            while True:
                next_dataset = next(names)
                payload = self.server.app.generator.generate_envelope(next_dataset)
                self.wfile.write((json.dumps(payload) + "\n").encode("utf-8"))
                self.wfile.flush()
                emitted += 1
                if limit and emitted >= limit:
                    break
                if interval:
                    time.sleep(interval)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _write_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    @staticmethod
    def _query_int(query: dict[str, list[str]], key: str, default: int) -> int:
        raw = query.get(key, [str(default)])[0]
        try:
            return max(0, int(raw))
        except ValueError:
            return default

    @staticmethod
    def _query_float(query: dict[str, list[str]], key: str, default: float) -> float:
        raw = query.get(key, [str(default)])[0]
        try:
            return max(0.0, float(raw))
        except ValueError:
            return default

    def log_message(self, format: str, *args: Any) -> None:
        return


class StreamingApp:
    def __init__(self, schema_path: str, rate: float) -> None:
        schema = load_schema(schema_path)
        self.generator = StreamingGenerator(schema=schema)
        self.rate = rate


def main() -> None:
    schema_path = str(Path(DEFAULT_SCHEMA).resolve())
    app = StreamingApp(schema_path=schema_path, rate=DEFAULT_RATE)
    server = StreamingHTTPServer((DEFAULT_HOST, DEFAULT_PORT), StreamingHandler, app=app)
    print(f"Streaming API listening on http://{DEFAULT_HOST}:{DEFAULT_PORT}")
    print("Paths:")
    print("  /health")
    print("  /datasets")
    print("  /events")
    for item in app.generator.dataset_info():
        print(f"  {item['path']}")
    server.serve_forever()


if __name__ == "__main__":
    main()
