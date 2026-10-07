import sqlite3
import json
import os
from typing import List, Optional, Dict, Any
from backend.app.config import settings
from backend.app.schemas.recruitment import POSITION_GROUPS
from backend.app.schemas.player import PlayerProfile, RawPlayerMetrics, NormalizedPlayerPercentiles

class FootballDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                primary_position TEXT NOT NULL,
                secondary_positions TEXT,
                club TEXT NOT NULL,
                league TEXT NOT NULL,
                nationality TEXT NOT NULL,
                preferred_foot TEXT NOT NULL,
                height_cm INTEGER,
                market_value_eur REAL NOT NULL,
                weekly_wage_eur REAL NOT NULL,
                contract_expiry_year INTEGER NOT NULL,
                release_clause_eur REAL,
                raw_metrics_json TEXT NOT NULL,
                normalized_percentiles_json TEXT NOT NULL,
                scouting_narrative TEXT NOT NULL
            );
            """)
            conn.commit()

    def insert_player(self, player: PlayerProfile):
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO players (
                id, name, age, primary_position, secondary_positions,
                club, league, nationality, preferred_foot, height_cm,
                market_value_eur, weekly_wage_eur, contract_expiry_year,
                release_clause_eur, raw_metrics_json, normalized_percentiles_json,
                scouting_narrative
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player.id,
                player.name,
                player.age,
                player.primary_position,
                json.dumps(player.secondary_positions),
                player.club,
                player.league,
                player.nationality,
                player.preferred_foot,
                player.height_cm,
                player.market_value_eur,
                player.weekly_wage_eur,
                player.contract_expiry_year,
                player.release_clause_eur,
                json.dumps(player.raw_metrics.model_dump()),
                json.dumps(player.normalized_percentiles.model_dump()),
                player.scouting_narrative
            ))
            conn.commit()

    def _row_to_player(self, row: sqlite3.Row) -> PlayerProfile:
        return PlayerProfile(
            id=row["id"],
            name=row["name"],
            age=row["age"],
            primary_position=row["primary_position"],
            secondary_positions=json.loads(row["secondary_positions"] or "[]"),
            club=row["club"],
            league=row["league"],
            nationality=row["nationality"],
            preferred_foot=row["preferred_foot"],
            height_cm=row["height_cm"],
            market_value_eur=row["market_value_eur"],
            weekly_wage_eur=row["weekly_wage_eur"],
            contract_expiry_year=row["contract_expiry_year"],
            release_clause_eur=row["release_clause_eur"],
            raw_metrics=RawPlayerMetrics(**json.loads(row["raw_metrics_json"])),
            normalized_percentiles=NormalizedPlayerPercentiles(**json.loads(row["normalized_percentiles_json"])),
            scouting_narrative=row["scouting_narrative"]
        )

    def get_player_by_id(self, player_id: str) -> Optional[PlayerProfile]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,))
            row = cur.fetchone()
            if row:
                return self._row_to_player(row)
            return None

    def get_all_players(self) -> List[PlayerProfile]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT * FROM players")
            return [self._row_to_player(r) for r in cur.fetchall()]

    def search_candidates_sql(
        self,
        position_family: Optional[str] = None,
        position: Optional[str] = None,
        max_age: Optional[int] = None,
        max_budget_eur: Optional[float] = None,
        max_wage_eur_pw: Optional[float] = None,
        min_minutes: Optional[int] = None
    ) -> List[PlayerProfile]:
        query = "SELECT * FROM players WHERE 1=1"
        params = []

        # Expand position_family → concrete position codes via POSITION_GROUPS
        target_positions: List[str] = []
        if position_family and position_family.upper() not in ("UNKNOWN", ""):
            target_positions = POSITION_GROUPS.get(position_family.upper(), [])
        if not target_positions and position and position.upper() not in ("UNKNOWN", ""):
            target_positions = [position.upper()]

        if target_positions:
            placeholders = ", ".join("?" * len(target_positions))
            like_clauses = " OR ".join(["secondary_positions LIKE ?" for _ in target_positions])
            query += f" AND (primary_position IN ({placeholders}) OR {like_clauses})"
            params.extend(target_positions)
            params.extend([f"%{p}%" for p in target_positions])

        if max_age is not None:
            query += " AND age <= ?"
            params.append(max_age)

        if max_budget_eur is not None:
            # Allow up to 15% budget stretch for scouting consideration
            query += " AND market_value_eur <= ?"
            params.append(max_budget_eur * 1.15)

        if max_wage_eur_pw is not None:
            query += " AND weekly_wage_eur <= ?"
            params.append(max_wage_eur_pw * 1.20)

        with self.get_connection() as conn:
            cur = conn.execute(query, params)
            players = [self._row_to_player(r) for r in cur.fetchall()]

        if min_minutes is not None:
            players = [p for p in players if p.raw_metrics.minutes_played >= min_minutes]

        # Post-filter: remove false positives from LIKE pattern matching
        # (e.g. %LW% incorrectly matching LWB in secondary_positions)
        if target_positions:
            players = [
                p for p in players
                if p.primary_position.upper() in target_positions
                or any(sp.upper() in target_positions for sp in p.secondary_positions)
            ]

        return players

db = FootballDatabase()
