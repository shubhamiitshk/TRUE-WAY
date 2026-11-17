"""TrueWay Guesthouse & Creator Affiliate Tracking System.

Handles affiliate registration, referral link/QR tracking, voucher activation
reconciliation, and revenue-share payout calculations.

Zero telemetry on tourist browsing: only tracks the aggregate referral source
and completed pass activations under transparent commercial terms.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

AFFILIATE_DB_PATH = Path(__file__).resolve().parent / "affiliates.sqlite"


@dataclass
class Affiliate:
    affiliate_id: str
    name: str
    category: str  # 'guesthouse', 'monastery', 'creator', 'tour_operator'
    location: str
    contact_person: str
    contact_phone: str
    payout_upi_or_bank: str
    commission_rate: float  # e.g., 0.30 for 30%
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ActivationEvent:
    event_id: str
    affiliate_id: str
    pack_id: str
    gross_amount_inr: float
    commission_inr: float
    timestamp: str
    payout_status: str = "PENDING"  # PENDING, APPROVED, PAID


class AffiliateManager:
    def __init__(self, db_path: Path = AFFILIATE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS affiliates (
                    affiliate_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    location TEXT NOT NULL,
                    contact_person TEXT,
                    contact_phone TEXT,
                    payout_upi_or_bank TEXT,
                    commission_rate REAL NOT NULL DEFAULT 0.30,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activation_events (
                    event_id TEXT PRIMARY KEY,
                    affiliate_id TEXT NOT NULL,
                    pack_id TEXT NOT NULL,
                    gross_amount_inr REAL NOT NULL,
                    commission_inr REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    payout_status TEXT NOT NULL DEFAULT 'PENDING',
                    FOREIGN KEY (affiliate_id) REFERENCES affiliates(affiliate_id)
                )
            """)
            conn.commit()

    def register_affiliate(self, affiliate: Affiliate) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO affiliates (
                    affiliate_id, name, category, location, contact_person,
                    contact_phone, payout_upi_or_bank, commission_rate, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                affiliate.affiliate_id, affiliate.name, affiliate.category,
                affiliate.location, affiliate.contact_person, affiliate.contact_phone,
                affiliate.payout_upi_or_bank, affiliate.commission_rate, affiliate.created_at
            ))
            conn.commit()
        return True

    def get_affiliate(self, affiliate_id: str) -> Optional[Affiliate]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM affiliates WHERE affiliate_id = ?", (affiliate_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Affiliate(
                affiliate_id=row["affiliate_id"],
                name=row["name"],
                category=row["category"],
                location=row["location"],
                contact_person=row["contact_person"],
                contact_phone=row["contact_phone"],
                payout_upi_or_bank=row["payout_upi_or_bank"],
                commission_rate=row["commission_rate"],
                created_at=row["created_at"],
            )

    def record_activation(
        self,
        event_id: str,
        affiliate_id: str,
        pack_id: str,
        gross_amount_inr: float = 299.0
    ) -> Optional[ActivationEvent]:
        aff = self.get_affiliate(affiliate_id)
        if not aff:
            return None
        commission = round(gross_amount_inr * aff.commission_rate, 2)
        event = ActivationEvent(
            event_id=event_id,
            affiliate_id=affiliate_id,
            pack_id=pack_id,
            gross_amount_inr=gross_amount_inr,
            commission_inr=commission,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payout_status="PENDING"
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO activation_events (
                    event_id, affiliate_id, pack_id, gross_amount_inr,
                    commission_inr, timestamp, payout_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.affiliate_id, event.pack_id,
                event.gross_amount_inr, event.commission_inr,
                event.timestamp, event.payout_status
            ))
            conn.commit()
        return event

    def get_affiliate_report(self, affiliate_id: str) -> Dict:
        aff = self.get_affiliate(affiliate_id)
        if not aff:
            return {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*), 
                    COALESCE(SUM(gross_amount_inr), 0), 
                    COALESCE(SUM(commission_inr), 0)
                FROM activation_events 
                WHERE affiliate_id = ?
            """, (affiliate_id,))
            total_activations, total_gross, total_commission = cursor.fetchone()

            cursor.execute("""
                SELECT COALESCE(SUM(commission_inr), 0)
                FROM activation_events
                WHERE affiliate_id = ? AND payout_status = 'PENDING'
            """, (affiliate_id,))
            pending_payout = cursor.fetchone()[0]

        return {
            "affiliate_id": aff.affiliate_id,
            "name": aff.name,
            "category": aff.category,
            "location": aff.location,
            "commission_rate": aff.commission_rate,
            "payout_account": aff.payout_upi_or_bank,
            "total_activations": total_activations,
            "total_gross_inr": total_gross,
            "total_commission_earned_inr": total_commission,
            "pending_payout_inr": pending_payout,
            "referral_url": f"https://trueway.travel/dl?aff={aff.affiliate_id}&src=standee"
        }

    def list_all_summaries(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT affiliate_id FROM affiliates ORDER BY name ASC")
            rows = cursor.fetchall()
        return [self.get_affiliate_report(row[0]) for row in rows]
