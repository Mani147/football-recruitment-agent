"""Initialize demo data once, and rebuild the process-local narrative index."""
from threading import Lock
from backend.app.data.sqlite_db import db
from backend.app.data.vector_store import vector_store

_lock = Lock()

def initialize_data(database=None, index=None):
    database = database if database is not None else db
    index = index if index is not None else vector_store
    with _lock:
        database.init_db()
        players = database.get_all_players()
        if not players:
            from backend.app.data.seed_database import PLAYERS_2526
            for player in PLAYERS_2526:
                database.insert_player(player)
            players = database.get_all_players()
        index.fit(players)
        return len(players)
