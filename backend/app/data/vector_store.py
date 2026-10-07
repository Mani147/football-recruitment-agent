import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.config import settings
from backend.app.schemas.player import PlayerProfile

class SemanticScoutVectorStore:
    def __init__(self):
        self.players: List[PlayerProfile] = []
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.tfidf_matrix = None
        self.is_fitted = False

    def fit(self, players: List[PlayerProfile]):
        self.players = players
        if not players:
            return
        corpus = [p.scouting_narrative for p in players]
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True

    def search_similar_profiles(self, query: str, top_k: int = 10) -> List[Tuple[PlayerProfile, float]]:
        if not self.is_fitted or not self.players:
            return []
        
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            results.append((self.players[idx], score))
        return results

    def hybrid_search(
        self,
        candidate_pool: List[PlayerProfile],
        query: str,
        top_k: int = 10
    ) -> List[Tuple[PlayerProfile, float]]:
        """
        Calculates semantic alignment score for an already filtered SQL candidate pool.
        """
        if not candidate_pool or not query:
            return [(p, 0.5) for p in candidate_pool[:top_k]]

        pool_corpus = [p.scouting_narrative for p in candidate_pool]
        try:
            pool_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            pool_matrix = pool_vectorizer.fit_transform(pool_corpus)
            query_vec = pool_vectorizer.transform([query])
            sims = cosine_similarity(query_vec, pool_matrix).flatten()
            
            scored_candidates = []
            for i, p in enumerate(candidate_pool):
                scored_candidates.append((p, float(sims[i])))
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            return scored_candidates[:top_k]
        except Exception:
            return [(p, 0.5) for p in candidate_pool[:top_k]]

vector_store = SemanticScoutVectorStore()
