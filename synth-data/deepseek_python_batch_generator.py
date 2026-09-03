#!/usr/bin/env python3
"""Generate synthetic batch datasets from schema.json with phone as primary natural key."""

from __future__ import annotations

import argparse
import csv
import json
import random
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any


COUNTRIES = ["IN", "US", "SG", "AE", "GB"]
CITIES = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune"]
STATES = ["Karnataka", "Maharashtra", "Delhi", "Telangana", "Tamil Nadu"]
FIRST_NAMES = ["Aarav", "Vivaan", "Isha", "Diya", "Arjun", "Mira", "Noah", "Emma"]
LAST_NAMES = ["Sharma", "Patel", "Reddy", "Mehta", "Kapoor", "Nair", "Brown", "Wilson"]
OCCUPATIONS = ["Engineer", "Analyst", "Manager", "Consultant", "Teacher", "Designer"]
COMPANIES = ["Acme Corp", "Globex", "Initech", "Umbrella", "Wayne Enterprises", "Stark Labs"]
CURRENCIES = ["INR", "USD", "SGD", "AED", "GBP"]
GENERIC_STATUSES = ["ACTIVE", "INACTIVE", "PENDING", "CLOSED"]
MARITAL_STATUSES = ["SINGLE", "MARRIED", "DIVORCED", "WIDOWED"]
SEGMENTS = ["MASS", "AFFLUENT", "HNI", "SME"]
IDENTIFIER_TYPES = ["PAN", "AADHAAR", "PASSPORT", "DRIVING_LICENSE", "CRM_ID"]
SOURCE_SYSTEMS = ["CRM", "LOS", "CBS", "MOBILE_APP", "PARTNER_PORTAL"]
OWNERSHIP_TYPES = ["SELF", "JOINT", "AUTHORIZED_USER"]
PAYMENT_METHODS = ["UPI", "ACH", "CARD", "NET_BANKING", "CASH"]
ACCOUNT_TYPES = ["HOME", "AUTO", "PERSONAL", "CARD", "MORTGAGE"]
ACCOUNT_STATUSES = ["ACTIVE", "CLOSED", "DELINQUENT", "DEFAULTED"]
PREMIUM_FREQUENCIES = ["MONTHLY", "QUARTERLY", "ANNUAL"]
CUSTOMER_STATUSES = ["ACTIVE", "DORMANT", "CHURN_RISK", "BLOCKED"]
CONSENT_TYPES = ["EMAIL_MARKETING", "SMS_MARKETING", "DATA_PROCESSING", "PROFILING"]
CONSENT_STATUSES = ["GRANTED", "REVOKED", "EXPIRED"]
PURPOSES = ["HOME_IMPROVEMENT", "EDUCATION", "MEDICAL", "TRAVEL", "WORKING_CAPITAL"]
PRODUCT_TYPES = ["LOAN", "INSURANCE", "CREDIT_CARD", "SAVINGS"]
CHANNELS = ["WEB", "MOBILE_APP", "BRANCH", "CALL_CENTER", "PARTNER", "API"]
PHONE_TYPES = ["MOBILE", "WORK", "HOME", "ALTERNATE"]
VERIFICATION_STATUSES = ["UNVERIFIED", "PENDING", "VERIFIED", "FAILED", "EXPIRED"]
CARRIERS = ["AIRTEL", "JIO", "VODAFONE", "TELENOR", "AT&T", "SINGTEL"]
VERIFICATION_METHODS = ["OTP", "BIOMETRIC", "DOCUMENT"]

# Country codes for phone numbers
PHONE_COUNTRY_CODES = {
    "IN": "91",
    "US": "1",
    "SG": "65",
    "AE": "971",
    "GB": "44"
}

# All possible external source systems
EXTERNAL_SOURCE_SYSTEMS = ["CRM", "LOS", "CBS", "MOBILE_APP", "PARTNER_PORTAL", "BUREAU", "INSURANCE_PARTNER"]

# Used phone numbers cache to ensure uniqueness
_used_phone_numbers: set[str] = set()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", default="schema.json", help="Path to schema.json")
    parser.add_argument("--dataset", default="all", help="Batch dataset name or 'all'")
    parser.add_argument("--rows", type=int, default=100, help="Rows per dataset")
    parser.add_argument(
        "--format",
        choices=["auto", "json", "csv", "parquet"],
        default="auto",
        help="Output format override",
    )
    parser.add_argument(
        "--output-dir",
        default="output/batch",
        help="Directory for generated files",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()


def load_schema(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class BatchGenerator:
    def __init__(self, schema: dict[str, Any], seed: int) -> None:
        self.schema = schema
        self.reference_values = schema.get("reference_values", {})
        self.random = random.Random(seed)
        self._customer_phones: dict[str, str] = {}  # Cache customer_id -> phone mapping
        self._email_suffix_counter = 0

    def generate_dataset(self, dataset_name: str, row_count: int) -> list[dict[str, Any]]:
        datasets = self.schema["datasets"]["batch"]
        if dataset_name not in datasets:
            raise KeyError(f"Unknown batch dataset: {dataset_name}")
        dataset = datasets[dataset_name]
        field_schema = dataset["schema"]
        return [self._generate_record(dataset_name, field_schema, index) for index in range(row_count)]

    def _generate_record(
        self,
        dataset_name: str,
        field_schema: dict[str, Any],
        index: int,
    ) -> dict[str, Any]:
        record: dict[str, Any] = {}
        for field_name, field_def in field_schema.items():
            # Handle both simple type strings and complex field definitions
            if isinstance(field_def, dict):
                field_type = field_def.get("type", "string")
                # Store metadata for special handling
                record[f"_{field_name}_meta"] = field_def
            else:
                field_type = field_def
            record[field_name] = self._generate_value(dataset_name, field_name, field_type, index, record)
        
        # Clean up metadata fields
        for field_name in list(record.keys()):
            if field_name.startswith("_"):
                del record[field_name]
                
        self._validate_record(field_schema, record)
        return record

    def _generate_value(
        self,
        dataset_name: str,
        field_name: str,
        field_type: str,
        index: int,
        record: dict[str, Any],
    ) -> Any:
        # Handle if field_type is actually a dict with type info
        if isinstance(field_type, dict):
            field_type = field_type.get("type", "string")
            
        base_type, nullable = self._normalize_type(field_type)
        if nullable and self.random.random() < 0.2:
            return None

        # Special handling for phone field - generate unique phone
        if field_name == "phone" and dataset_name == "customers":
            return self._generate_unique_phone_number()
            
        # For other datasets, phone is a matching key - use existing phone from customers if available
        if field_name == "phone" and dataset_name != "customers" and dataset_name != "phone_master":
            # Try to use a customer phone if we have one, otherwise generate one
            customer_id = record.get("customer_id")
            if customer_id and customer_id in self._customer_phones:
                return self._customer_phones[customer_id]
            return self._generate_unique_phone_number()

        if field_name.endswith("_id") or field_name == "id":
            return self._generate_identifier(field_name, index)
        if field_name.endswith("_date") or base_type == "date":
            return self._generate_date(field_name)
        if field_name.endswith("_at") or field_name == "event_time" or base_type == "timestamp":
            return self._generate_timestamp(field_name)
        if base_type == "boolean":
            return self.random.choice([True, False])
        if base_type == "integer":
            return self._generate_integer(field_name)
        if base_type == "decimal":
            return self._generate_decimal(field_name)
        if base_type == "object":
            return self._generate_object(dataset_name, field_name, record)
        return self._generate_string(dataset_name, field_name, index, record)

    def _generate_unique_phone_number(self) -> str:
        """Generate a unique phone number with country code."""
        # Choose a random country code
        country_code = self.random.choice(list(PHONE_COUNTRY_CODES.values()))
        
        # Generate 10-digit number
        attempts = 0
        while attempts < 100:
            number = f"+{country_code}{self.random.randint(6000000000, 9999999999)}"
            if number not in _used_phone_numbers:
                _used_phone_numbers.add(number)
                return number
            attempts += 1
        
        # Fallback: generate with timestamp to ensure uniqueness
        number = f"+{country_code}{int(datetime.now().timestamp()) % 10000000000:010d}"
        _used_phone_numbers.add(number)
        return number

    @staticmethod
    def _normalize_type(field_type: str) -> tuple[str, bool]:
        if isinstance(field_type, dict):
            field_type = field_type.get("type", "string")
        parts = field_type.split("|")
        nullable = "null" in parts
        base_type = next(part for part in parts if part != "null")
        return base_type, nullable

    def _generate_identifier(self, field_name: str, index: int) -> str:
        prefix = field_name.removesuffix("_id").upper() or "ID"
        token = uuid.UUID(int=self.random.getrandbits(128)).hex[:12]
        return f"{prefix}_{index:06d}_{token}"

    def _generate_date(self, field_name: str) -> str:
        if "birth" in field_name:
            start = date(1960, 1, 1)
            end = date(2004, 12, 31)
        elif "maturity" in field_name or "expiry" in field_name or "expiration" in field_name:
            start = date.today()
            end = date.today() + timedelta(days=3650)
        elif "opening" in field_name or "open" in field_name:
            start = date.today() - timedelta(days=3650)
            end = date.today()
        elif "closing" in field_name or "close" in field_name:
            start = date.today() - timedelta(days=365)
            end = date.today() + timedelta(days=365)
        elif "effective" in field_name:
            start = date.today() - timedelta(days=365)
            end = date.today()
        elif "enquiry" in field_name or "report" in field_name:
            start = date.today() - timedelta(days=365)
            end = date.today()
        elif "verification" in field_name or "verified" in field_name:
            start = date.today() - timedelta(days=30)
            end = date.today()
        else:
            start = date.today() - timedelta(days=3650)
            end = date.today() + timedelta(days=365)
        return self._random_date(start, end).isoformat()

    def _generate_timestamp(self, field_name: str) -> str:
        if "registration" in field_name or "created" in field_name or "application" in field_name:
            start = datetime.now() - timedelta(days=730)
        elif "updated" in field_name or "last_updated" in field_name:
            start = datetime.now() - timedelta(days=30)
        else:
            start = datetime.now() - timedelta(days=90)
        end = datetime.now()
        seconds = int((end - start).total_seconds())
        stamp = start + timedelta(seconds=self.random.randint(0, max(seconds, 1)))
        return stamp.replace(microsecond=0).isoformat()

    def _generate_integer(self, field_name: str) -> int:
        if "score" in field_name:
            return self.random.randint(300, 900)
        if "days_past_due" in field_name or "days_late" in field_name:
            return self.random.randint(0, 120)
        if "months" in field_name or "tenure" in field_name:
            return self.random.randint(6, 360)
        if "dependents" in field_name:
            return self.random.randint(0, 5)
        if "year" in field_name:
            return self.random.randint(2000, date.today().year)
        if "count" in field_name:
            return self.random.randint(0, 12)
        if "attempt" in field_name:
            return self.random.randint(0, 5)
        return self.random.randint(0, 100)

    def _generate_decimal(self, field_name: str) -> float:
        if "interest_rate" in field_name:
            value = self.random.uniform(7.0, 24.0)
        elif "ratio" in field_name:
            value = self.random.uniform(0.0, 1.0)
        elif "income" in field_name:
            value = self.random.uniform(250000, 5000000)
        elif "balance" in field_name or "outstanding" in field_name:
            value = self.random.uniform(1000, 2500000)
        elif "amount" in field_name or "limit" in field_name or "value" in field_name:
            value = self.random.uniform(500, 5000000)
        elif "premium" in field_name:
            value = self.random.uniform(1000, 100000)
        elif "sum_assured" in field_name or "coverage" in field_name:
            value = self.random.uniform(100000, 10000000)
        else:
            value = self.random.uniform(0, 100000)
        return float(Decimal(str(value)).quantize(Decimal("0.01")))

    def _generate_object(self, dataset_name: str, field_name: str, record: dict[str, Any]) -> dict[str, Any]:
        if field_name == "changed_fields":
            return {
                "field": self.random.choice(["email", "phone", "address_line_1", "customer_segment"]),
                "old_value": self.random.choice(["old@example.com", "9999999999", "Segment_A"]),
                "new_value": self.random.choice(["new@example.com", "8888888888", "Segment_B"]),
            }
        if field_name == "metadata":
            return {
                "trace_id": uuid.UUID(int=self.random.getrandbits(128)).hex,
                "source": self.random.choice(["mobile", "web", "crm", "partner"]),
                "priority": self.random.choice(["low", "medium", "high"]),
                "timestamp": self._generate_timestamp("metadata_timestamp"),
            }
        return {
            "dataset": dataset_name,
            "field": field_name,
            "source": record.get("source_system", self.random.choice(SOURCE_SYSTEMS)),
            "score": round(self.random.uniform(0, 1), 3),
        }

    def _generate_string(
        self,
        dataset_name: str,
        field_name: str,
        index: int,
        record: dict[str, Any],
    ) -> str:
        lower_name = field_name.lower()
        
        # Handle phone fields (for non-customer datasets)
        if "phone" in lower_name and field_name != "phone":
            return self._generate_unique_phone_number()
            
        if field_name == "first_name":
            return self.random.choice(FIRST_NAMES)
        if field_name == "middle_name":
            return self.random.choice(["K", "R", "M", "A", "Singh", "Kumar", "Prasad"])
        if field_name == "last_name":
            return self.random.choice(LAST_NAMES)
        if field_name == "email":
            first = record.get("first_name", self.random.choice(FIRST_NAMES)).lower()
            last = record.get("last_name", self.random.choice(LAST_NAMES)).lower()
            self._email_suffix_counter += 1
            return f"{first}.{last}{self._email_suffix_counter}@example.com"
        if "address_line_1" == field_name:
            return f"{self.random.randint(10, 999)}, Market Road"
        if "address_line_2" == field_name:
            return self.random.choice(["Suite 10", "Block B", "Floor 3", "Apartment 5A", "Tower 2"])
        if field_name == "city":
            return self.random.choice(CITIES)
        if field_name == "state":
            return self.random.choice(STATES)
        if field_name == "postal_code":
            return str(self.random.randint(100000, 999999))
        if field_name in {"country", "registration_country", "ip_country", "target_country"}:
            return self.random.choice(COUNTRIES)
        if field_name == "nationality":
            return self.random.choice(COUNTRIES)
        if field_name == "occupation" or field_name == "job_title":
            return self.random.choice(OCCUPATIONS)
        if field_name == "industry":
            return self.random.choice(["Technology", "Banking", "Healthcare", "Retail", "Education"])
        if field_name == "employment_type":
            return self._pick_reference("employment_types", fallback=ACCOUNT_TYPES)
        if field_name == "employer_name":
            return self.random.choice(COMPANIES)
        if field_name == "income_currency" or field_name == "currency":
            return self.random.choice(CURRENCIES)
        if field_name == "marital_status":
            return self.random.choice(MARITAL_STATUSES)
        if field_name == "customer_segment":
            return self.random.choice(SEGMENTS)
        if field_name == "customer_status":
            return self.random.choice(CUSTOMER_STATUSES)
        if field_name == "gender":
            return self.random.choice(["MALE", "FEMALE", "NON_BINARY"])
        if field_name == "source_system":
            return self.random.choice(SOURCE_SYSTEMS)
        if field_name == "identifier_type":
            return self.random.choice(IDENTIFIER_TYPES)
        if field_name == "identifier_value":
            return uuid.UUID(int=self.random.getrandbits(128)).hex[:16].upper()
        if field_name == "bureau":
            return self._pick_reference("credit_bureaus", fallback=["SYNTHETIC_BUREAU"])
        if field_name == "score_band":
            return self.random.choice(["POOR", "FAIR", "GOOD", "VERY_GOOD", "EXCELLENT"])
        if field_name == "account_type":
            if dataset_name == "bank_accounts":
                return self._pick_reference("bank_account_types", fallback=ACCOUNT_TYPES)
            return self.random.choice(ACCOUNT_TYPES)
        if field_name == "account_status":
            return self.random.choice(ACCOUNT_STATUSES)
        if field_name == "ownership_type":
            return self.random.choice(OWNERSHIP_TYPES)
        if field_name == "loan_type":
            return self._pick_reference("loan_types", fallback=ACCOUNT_TYPES)
        if field_name == "loan_status":
            return self._pick_reference("loan_status", fallback=GENERIC_STATUSES)
        if field_name == "application_channel" or field_name == "channel":
            return self._pick_reference("customer_channels", fallback=CHANNELS)
        if field_name == "application_status":
            return self._pick_reference("loan_application_status", fallback=GENERIC_STATUSES)
        if field_name == "rejection_reason":
            return self.random.choice(["LOW_SCORE", "HIGH_DTI", "INCOMPLETE_DOCS", "POLICY_RULE"])
        if field_name == "payment_status":
            return self.random.choice(["PAID", "PARTIAL", "DUE", "FAILED"])
        if field_name == "payment_method":
            return self.random.choice(PAYMENT_METHODS)
        if field_name == "bank_name":
            return self.random.choice(["Axis Bank", "HDFC Bank", "ICICI Bank", "DBS Bank"])
        if field_name == "bank_type":
            return self.random.choice(["PRIVATE", "PUBLIC", "DIGITAL"])
        if field_name == "lender_name":
            return self.random.choice(["LendFast", "HomeTrust", "AutoCredit", "CapitalOne Synthetic"])
        if field_name == "lender_type":
            return self.random.choice(["BANK", "NBFC", "FINTECH"])
        if field_name == "insurer_name":
            return self.random.choice(["LifeShield", "HealthCover", "SafeDrive", "TrustInsure"])
        if field_name == "insurer_type":
            return self.random.choice(["LIFE", "GENERAL", "HEALTH"])
        if field_name == "policy_type":
            return self._pick_reference("insurance_types", fallback=["LIFE"])
        if field_name == "policy_status":
            return self.random.choice(["ACTIVE", "EXPIRED", "LAPSED", "CLAIMED"])
        if field_name == "premium_frequency":
            return self.random.choice(PREMIUM_FREQUENCIES)
        if field_name == "claim_type":
            return self.random.choice(["ACCIDENT", "HOSPITALIZATION", "THEFT", "DAMAGE"])
        if field_name == "claim_status":
            return self.random.choice(["FILED", "UNDER_REVIEW", "SETTLED", "REJECTED"])
        if field_name == "vehicle_type":
            return self.random.choice(["CAR", "BIKE", "TRUCK", "SUV"])
        if field_name == "manufacturer":
            return self.random.choice(["Toyota", "Hyundai", "Honda", "Tata", "Ford"])
        if field_name == "model":
            return self.random.choice(["Model X", "Civic", "Nexon", "Creta", "Corolla"])
        if field_name == "fuel_type":
            return self.random.choice(["PETROL", "DIESEL", "EV", "HYBRID"])
        if field_name == "property_type":
            return self.random.choice(["APARTMENT", "VILLA", "PLOT", "COMMERCIAL"])
        if field_name == "employment_status":
            return self.random.choice(["CURRENT", "FORMER"])
        if field_name == "license_type":
            return self.random.choice(["FULL", "LIMITED", "REGIONAL"])
        if field_name == "campaign_name":
            return f"Campaign {index:04d}"
        if field_name == "campaign_type":
            return self.random.choice(["ACQUISITION", "CROSS_SELL", "UPSELL", "RETENTION"])
        if field_name == "product_type" or field_name == "product":
            return self.random.choice(PRODUCT_TYPES)
        if field_name == "consent_type":
            return self.random.choice(CONSENT_TYPES)
        if field_name == "consent_status":
            return self.random.choice(CONSENT_STATUSES)
        if field_name == "purpose":
            return self.random.choice(PURPOSES)
        if field_name == "branch_code":
            return f"BR{self.random.randint(100, 999)}"
        if field_name == "status":
            return self.random.choice(GENERIC_STATUSES)
        if field_name == "transaction_type":
            return self._pick_reference("transaction_types", fallback=["DEBIT", "CREDIT"])
        if field_name == "event_type":
            return self._event_type_for_dataset(dataset_name)
        if field_name == "page":
            return self.random.choice(["/home", "/loans", "/credit-score", "/insurance"])
        if field_name == "source":
            return self.random.choice(["GOOGLE", "META", "AFFILIATE", "CRM"])
        if field_name == "device_type":
            return self.random.choice(["ANDROID", "IOS", "WEB"])
        if field_name == "operation":
            return self.random.choice(["INSERT", "UPDATE", "DELETE"])
        if field_name == "merchant_name":
            return self.random.choice(["Amazon", "Swiggy", "Uber", "Apple", "Walmart"])
        if field_name == "merchant_category":
            return self.random.choice(["GROCERY", "TRAVEL", "RETAIL", "DINING", "UTILITIES"])
        if field_name == "location":
            return self.random.choice(CITIES)
        if field_name == "lender_id":
            return f"LENDER_{self.random.randint(100, 999)}"
        if field_name == "insurer_id":
            return f"INSURER_{self.random.randint(100, 999)}"
        if field_name == "bank_id":
            return f"BANK_{self.random.randint(100, 999)}"
        if field_name == "external_source_id":
            return f"EXT_{uuid.UUID(int=self.random.getrandbits(128)).hex[:8].upper()}"
        if field_name == "external_source_system":
            return self.random.choice(EXTERNAL_SOURCE_SYSTEMS)
        if field_name == "phone_type":
            return self.random.choice(PHONE_TYPES)
        if field_name == "verification_status":
            return self.random.choice(VERIFICATION_STATUSES)
        if field_name == "carrier":
            return self.random.choice(CARRIERS)
        if field_name == "verification_method":
            return self.random.choice(VERIFICATION_METHODS)
        if field_name == "ip_address":
            return f"192.168.{self.random.randint(1, 255)}.{self.random.randint(1, 255)}"
        if field_name == "device_id":
            return f"DEV_{uuid.UUID(int=self.random.getrandbits(128)).hex[:12]}"
        if "type" in lower_name:
            return self.random.choice(["TYPE_A", "TYPE_B", "TYPE_C"])
        if "name" in lower_name:
            return f"{field_name}_{index:06d}"
        return f"{field_name}_{index:06d}"

    def _event_type_for_dataset(self, dataset_name: str) -> str:
        if dataset_name == "customer_behavior_events":
            return self._pick_reference("behavior_events", fallback=["LOGIN"])
        if dataset_name == "marketing_events":
            return self._pick_reference("marketing_events", fallback=["CAMPAIGN_SENT"])
        if dataset_name == "credit_events":
            return self._pick_reference("credit_event_types", fallback=["CREDIT_SCORE_UPDATED"])
        return self.random.choice(["CREATED", "UPDATED", "VIEWED", "SUBMITTED"])

    def _pick_reference(self, key: str, fallback: list[str]) -> str:
        values = self.reference_values.get(key, fallback)
        return self.random.choice(values)

    @staticmethod
    def _random_date(start: date, end: date) -> date:
        day_delta = (end - start).days
        return start + timedelta(days=random.randint(0, max(day_delta, 1)))

    @staticmethod
    def _validate_record(field_schema: dict[str, Any], record: dict[str, Any]) -> None:
        for field_name, field_def in field_schema.items():
            if isinstance(field_def, dict):
                field_type = field_def.get("type", "string")
                # Check if field is required for external sources
                if field_def.get("required_for_external_sources", False):
                    if record.get(field_name) is None:
                        raise ValueError(f"Field {field_name} is required for external sources but is null")
            else:
                field_type = field_def
            _, nullable = BatchGenerator._normalize_type(field_type)
            if record.get(field_name) is None and not nullable:
                raise ValueError(f"Field {field_name} is null but declared as {field_type}")


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        # Handle nested objects by converting to JSON strings
        processed_rows = []
        for row in rows:
            processed = {}
            for key, value in row.items():
                if isinstance(value, (dict, list)):
                    processed[key] = json.dumps(value)
                else:
                    processed[key] = value
            processed_rows.append(processed)
        writer = csv.DictWriter(handle, fieldnames=list(processed_rows[0].keys()))
        writer.writeheader()
        writer.writerows(processed_rows)


def write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("Parquet output requires pandas and pyarrow installed.") from exc
    frame = pd.DataFrame(rows)
    frame.to_parquet(path, index=False)


def main() -> None:
    args = parse_args()
    schema = load_schema(args.schema)
    generator = BatchGenerator(schema=schema, seed=args.seed)
    batch_datasets = schema["datasets"]["batch"]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_names = list(batch_datasets) if args.dataset == "all" else [args.dataset]
    writers = {"json": write_json, "csv": write_csv, "parquet": write_parquet}

    for dataset_name in dataset_names:
        dataset_meta = batch_datasets[dataset_name]
        output_format = dataset_meta.get("format", "json") if args.format == "auto" else args.format
        rows = generator.generate_dataset(dataset_name, args.rows)
        output_path = output_dir / f"{dataset_name}.{output_format}"
        writers[output_format](output_path, rows)
        print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()