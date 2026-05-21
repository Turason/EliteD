"""
Journal ingestion utilities for Elite Dangerous player data.

This module parses local journal and status files and maps the most important
fields directly into the existing AI integration models.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_integration.models import EventType, PlayerAction, PlayerStatus, SystemState


COMBAT_RANKS = [
    "Harmless",
    "Mostly Harmless",
    "Novice",
    "Competent",
    "Expert",
    "Master",
    "Dangerous",
    "Deadly",
    "Elite",
]

TRADE_RANKS = [
    "Penniless",
    "Mostly Penniless",
    "Peddler",
    "Dealer",
    "Merchant",
    "Broker",
    "Entrepreneur",
    "Tycoon",
    "Elite",
]

EXPLORATION_RANKS = [
    "Aimless",
    "Mostly Aimless",
    "Scout",
    "Surveyor",
    "Trailblazer",
    "Pathfinder",
    "Ranger",
    "Pioneer",
    "Elite",
]


@dataclass
class IngestSummary:
    """Summary of what was parsed and mapped from source files."""

    events_read: int = 0
    actions_created: int = 0
    skipped_events: int = 0


class JournalIngestor:
    """Parse journal/status data and map into existing model objects."""

    def __init__(self) -> None:
        self.summary = IngestSummary()

    def ingest_journal_file(
        self,
        journal_path: str,
        player_status: Optional[PlayerStatus] = None,
        system_state: Optional[SystemState] = None,
        max_recent_actions: int = 20,
    ) -> tuple[PlayerStatus, SystemState, IngestSummary]:
        """Read a line-delimited journal file and update model objects in place."""
        path = Path(journal_path)
        if not path.exists():
            raise FileNotFoundError(f"Journal file not found: {journal_path}")

        self.summary = IngestSummary()

        player = player_status or PlayerStatus(name="Unknown Commander", current_system="Unknown")
        system = system_state or SystemState(name=player.current_system)

        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                event_data = self._safe_load_json(line)
                if not event_data:
                    self.summary.skipped_events += 1
                    continue

                self.summary.events_read += 1
                self._apply_event(event_data, player, system)

        # Keep recent actions bounded for prompt efficiency.
        if len(player.recent_actions) > max_recent_actions:
            player.recent_actions = player.recent_actions[-max_recent_actions:]

        return player, system, self.summary

    def ingest_status_file(self, status_path: str, player_status: PlayerStatus) -> PlayerStatus:
        """Read Status.json and map the available immediate state onto PlayerStatus."""
        path = Path(status_path)
        if not path.exists():
            raise FileNotFoundError(f"Status file not found: {status_path}")

        raw_data = path.read_text(encoding="utf-8").strip()
        status = self._safe_load_json(raw_data)
        if not status:
            return player_status

        fuel = status.get("Fuel") or {}
        fuel_main = fuel.get("FuelMain")
        if fuel_main is not None:
            action = PlayerAction(
                event_type=EventType.EXPLORATION,
                description=f"Status update: fuel main tank at {fuel_main:.2f}t",
                timestamp=status.get("timestamp", ""),
                location=player_status.current_system,
            )
            player_status.recent_actions.append(action)

        # Decode commonly used flags for contextual state as actions.
        flags = int(status.get("Flags", 0))
        if flags & 1:  # Docked
            station_name = status.get("StationName")
            if station_name:
                player_status.current_station = station_name
        if flags & 16:  # Supercruise
            player_status.current_station = None

        return player_status

    def _apply_event(self, event: Dict[str, Any], player: PlayerStatus, system: SystemState) -> None:
        event_name = event.get("event", "")
        ts = event.get("timestamp", "")

        if event_name == "LoadGame":
            player.name = event.get("Commander", player.name)
            player.credits = float(event.get("Credits", player.credits))
            player.ship_type = event.get("Ship", player.ship_type)
            return

        if event_name in {"Location", "FSDJump", "CarrierJump"}:
            star_system = event.get("StarSystem")
            if star_system:
                player.current_system = star_system
                system.name = star_system

            system.allegiance = event.get("SystemAllegiance", system.allegiance)
            system.government = event.get("SystemGovernment", system.government)
            system.economy = event.get("SystemEconomy_Localised", event.get("SystemEconomy", system.economy))
            system.security_level = event.get("SystemSecurity_Localised", event.get("SystemSecurity", system.security_level))
            system.population = int(event.get("Population", system.population or 0))

            action = PlayerAction(
                event_type=EventType.JUMP,
                description=f"Jumped to {player.current_system}",
                timestamp=ts,
                location=player.current_system,
                value=float(event.get("JumpDist", 0.0)) if event.get("JumpDist") is not None else None,
            )
            player.recent_actions.append(action)
            self.summary.actions_created += 1
            return

        if event_name == "Docked":
            player.current_station = event.get("StationName", player.current_station)
            system.controlling_faction = event.get("StationFaction", {}).get("Name", system.controlling_faction)
            return

        if event_name == "Undocked":
            player.current_station = None
            return

        if event_name == "Rank":
            combat = event.get("Combat")
            trade = event.get("Trade")
            explore = event.get("Explore")
            player.combat_rank = self._rank_name(combat, COMBAT_RANKS, player.combat_rank)
            player.trade_rank = self._rank_name(trade, TRADE_RANKS, player.trade_rank)
            player.exploration_rank = self._rank_name(explore, EXPLORATION_RANKS, player.exploration_rank)
            return

        if event_name == "Reputation":
            player.federation_rep = float(event.get("Federation", player.federation_rep))
            player.empire_rep = float(event.get("Empire", player.empire_rep))
            player.alliance_rep = float(event.get("Alliance", player.alliance_rep))
            return

        action = self._event_to_action(event_name, event, ts, player.current_system)
        if action:
            player.recent_actions.append(action)
            self.summary.actions_created += 1
        else:
            self.summary.skipped_events += 1

    def _event_to_action(
        self,
        event_name: str,
        event: Dict[str, Any],
        timestamp: str,
        current_system: str,
    ) -> Optional[PlayerAction]:
        if event_name in {"MissionAccepted", "MissionCompleted", "MissionFailed"}:
            return PlayerAction(
                event_type=EventType.MISSION,
                description=event_name,
                timestamp=timestamp,
                location=current_system,
                target=event.get("Faction"),
                value=float(event.get("Reward", 0.0)) if event.get("Reward") is not None else None,
            )

        if event_name in {"MarketSell", "MarketBuy", "SellDrones", "BuyDrones"}:
            item = event.get("Type_Localised", event.get("Type", "goods"))
            return PlayerAction(
                event_type=EventType.TRADE,
                description=f"{event_name}: {item}",
                timestamp=timestamp,
                location=current_system,
                value=float(event.get("TotalSale", event.get("TotalCost", 0.0))) if any(
                    k in event for k in ("TotalSale", "TotalCost")
                ) else None,
            )

        if event_name in {"Bounty", "FactionKillBond", "Died", "Interdicted", "EscapeInterdiction"}:
            return PlayerAction(
                event_type=EventType.COMBAT,
                description=event_name,
                timestamp=timestamp,
                location=current_system,
                target=event.get("VictimFaction") or event.get("Faction"),
                value=float(event.get("TotalReward", event.get("Reward", 0.0))) if any(
                    k in event for k in ("TotalReward", "Reward")
                ) else None,
            )

        if event_name in {"Scan", "ScanOrganic", "CodexEntry", "SellExplorationData"}:
            body_name = event.get("BodyName") or event.get("Name")
            desc = event_name if not body_name else f"{event_name}: {body_name}"
            return PlayerAction(
                event_type=EventType.EXPLORATION,
                description=desc,
                timestamp=timestamp,
                location=current_system,
            )

        return None

    @staticmethod
    def _safe_load_json(text: str) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _rank_name(value: Any, rank_map: List[str], fallback: str) -> str:
        if not isinstance(value, int):
            return fallback
        if value < 0 or value >= len(rank_map):
            return fallback
        return rank_map[value]
