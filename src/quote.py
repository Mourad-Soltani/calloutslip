# Mourad.Soltani — CalloutSlip quote engine
"""Pure pricing core for after-hours trade call-out quotes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


MONEY = Decimal("0.01")

WINDOWS = {
    "standard": Decimal("1.00"),
    "evening": Decimal("1.35"),
    "night": Decimal("1.60"),
    "weekend": Decimal("1.75"),
    "holiday": Decimal("2.00"),
}

TRADES = {
    "locksmith": "Locksmith",
    "plumber": "Plumber",
    "electrician": "Electrician",
    "glazier": "Glazier",
    "hvac": "HVAC",
    "appliance": "Appliance repair",
}


class QuoteError(ValueError):
    """Invalid quote input."""


def money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


def _non_negative(name: str, value: Decimal) -> Decimal:
    if value < 0:
        raise QuoteError(f"{name} cannot be negative")
    return value


@dataclass(frozen=True)
class QuoteInput:
    trade: str
    customer: str
    job_summary: str
    window: str
    callout_fee: Decimal
    miles: Decimal
    mileage_rate: Decimal
    labor_hours: Decimal
    labor_rate: Decimal
    parts_cost: Decimal
    parts_markup: Decimal
    tax_rate: Decimal
    deposit_rate: Decimal
    minimum_charge: Decimal

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "QuoteInput":
        trade = str(raw.get("trade", "")).strip().lower()
        if trade not in TRADES:
            raise QuoteError(f"trade must be one of {sorted(TRADES)}")
        window = str(raw.get("window", "")).strip().lower()
        if window not in WINDOWS:
            raise QuoteError(f"window must be one of {sorted(WINDOWS)}")
        customer = str(raw.get("customer", "")).strip()
        summary = str(raw.get("job_summary", "")).strip()
        if not customer or not summary:
            raise QuoteError("customer and job_summary are required")
        return cls(
            trade=trade,
            customer=customer,
            job_summary=summary,
            window=window,
            callout_fee=_non_negative("callout_fee", money(raw.get("callout_fee", 0))),
            miles=_non_negative("miles", money(raw.get("miles", 0))),
            mileage_rate=_non_negative("mileage_rate", money(raw.get("mileage_rate", 0))),
            labor_hours=_non_negative("labor_hours", money(raw.get("labor_hours", 0))),
            labor_rate=_non_negative("labor_rate", money(raw.get("labor_rate", 0))),
            parts_cost=_non_negative("parts_cost", money(raw.get("parts_cost", 0))),
            parts_markup=_non_negative("parts_markup", money(raw.get("parts_markup", 0))),
            tax_rate=_non_negative("tax_rate", money(raw.get("tax_rate", 0))),
            deposit_rate=_non_negative("deposit_rate", money(raw.get("deposit_rate", 0))),
            minimum_charge=_non_negative("minimum_charge", money(raw.get("minimum_charge", 0))),
        )


@dataclass(frozen=True)
class Quote:
    trade_label: str
    customer: str
    job_summary: str
    window: str
    multiplier: str
    callout_fee: str
    travel: str
    labor: str
    parts: str
    subtotal_before_window: str
    window_premium: str
    taxable: str
    tax: str
    total: str
    deposit_due: str
    balance_on_completion: str
    minimum_applied: bool
    slip: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_quote(raw: dict[str, Any]) -> Quote:
    data = QuoteInput.from_dict(raw)
    if data.deposit_rate > Decimal("1"):
        raise QuoteError("deposit_rate must be between 0 and 1")
    if data.tax_rate > Decimal("0.30"):
        raise QuoteError("tax_rate above 30% looks like a percent, use 0.20 for 20%")
    if data.parts_markup > Decimal("3"):
        raise QuoteError("parts_markup above 3.00 is rejected")

    multiplier = WINDOWS[data.window]
    travel = money(data.miles * data.mileage_rate)
    labor = money(data.labor_hours * data.labor_rate)
    parts = money(data.parts_cost * (Decimal("1") + data.parts_markup))
    before = money(data.callout_fee + travel + labor + parts)
    adjusted = money(before * multiplier)
    minimum_applied = adjusted < data.minimum_charge
    taxable = data.minimum_charge if minimum_applied else adjusted
    taxable = money(taxable)
    window_premium = money(taxable - before) if not minimum_applied else money(taxable - before)
    tax = money(taxable * data.tax_rate)
    total = money(taxable + tax)
    deposit = money(total * data.deposit_rate)
    balance = money(total - deposit)

    slip = "\n".join(
        [
            "CALLOUTSLIP",
            f"Trade: {TRADES[data.trade]}",
            f"Customer: {data.customer}",
            f"Job: {data.job_summary}",
            f"Window: {data.window} (x{multiplier})",
            f"Call-out: {data.callout_fee}",
            f"Travel: {travel}",
            f"Labor: {labor}",
            f"Parts: {parts}",
            f"Before window: {before}",
            f"Window premium: {window_premium}",
            f"Minimum applied: {'yes' if minimum_applied else 'no'}",
            f"Taxable: {taxable}",
            f"Tax: {tax}",
            f"Total: {total}",
            f"Deposit due: {deposit}",
            f"Balance on completion: {balance}",
            "Prepared by CalloutSlip · Mourad.Soltani",
        ]
    )
    return Quote(
        trade_label=TRADES[data.trade],
        customer=data.customer,
        job_summary=data.job_summary,
        window=data.window,
        multiplier=str(multiplier),
        callout_fee=str(data.callout_fee),
        travel=str(travel),
        labor=str(labor),
        parts=str(parts),
        subtotal_before_window=str(before),
        window_premium=str(window_premium),
        taxable=str(taxable),
        tax=str(tax),
        total=str(total),
        deposit_due=str(deposit),
        balance_on_completion=str(balance),
        minimum_applied=minimum_applied,
        slip=slip,
    )
