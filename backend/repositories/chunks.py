import re

import psycopg

from backend.config import settings


class ChunkRepository:
    def create_chunk(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        embedding: list[float],
    ) -> int:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chunks (
                        document_id,
                        chunk_index,
                        content,
                        embedding
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s::vector
                    )
                    RETURNING id
                    """,
                    (
                        document_id,
                        chunk_index,
                        content,
                        embedding,
                    ),
                )

                chunk_id = cursor.fetchone()[0]

            connection.commit()

        return chunk_id

    def search_chunks(
        self,
        embedding: list[float],
        limit: int = 10,
        distance_threshold: float | None = None,
        document_ids: list[int] | None = None,
    ):
        if distance_threshold is None:
            distance_threshold = settings.retrieval_distance_threshold

        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                if document_ids:
                    cursor.execute(
                        """
                        SELECT
                            id,
                            document_id,
                            chunk_index,
                            content,
                            embedding <=> %s::vector AS distance
                        FROM chunks
                        WHERE embedding IS NOT NULL
                          AND document_id = ANY(%s)
                          AND embedding <=> %s::vector <= %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                        """,
                        (
                            embedding,
                            document_ids,
                            embedding,
                            distance_threshold,
                            embedding,
                            limit,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT
                            id,
                            document_id,
                            chunk_index,
                            content,
                            embedding <=> %s::vector AS distance
                        FROM chunks
                        WHERE embedding IS NOT NULL
                          AND embedding <=> %s::vector <= %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                        """,
                        (
                            embedding,
                            embedding,
                            distance_threshold,
                            embedding,
                            limit,
                        ),
                    )

                return cursor.fetchall()

    def keyword_search_chunks(
        self,
        query: str,
        limit: int = 10,
        document_ids: list[int] | None = None,
    ):
        keywords = self._extract_keywords(query)

        if not keywords:
            return []

        conditions = []
        parameters = []

        for keyword in keywords:
            conditions.append(
                "LOWER(content) LIKE %s"
            )
            parameters.append(f"%{keyword}%")

        document_filter = ""

        if document_ids:
            document_filter = """
                AND document_id = ANY(%s)
            """
            parameters.append(document_ids)

        sql = f"""
            SELECT
                id,
                document_id,
                chunk_index,
                content,
                0.0::double precision AS distance
            FROM chunks
            WHERE (
                {" OR ".join(conditions)}
            )
            {document_filter}
            ORDER BY id
            LIMIT %s
        """

        parameters.append(limit)

        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    parameters,
                )

                return cursor.fetchall()

    def hybrid_search_chunks(
        self,
        embedding: list[float],
        query: str,
        limit: int = 5,
        distance_threshold: float | None = None,
        document_ids: list[int] | None = None,
    ):
        """
        Hybrid retrieval.

        Combines:
        - semantic vector similarity
        - exact keyword matching

        Results are merged and ranked using both signals.
        """

        semantic_rows = self.search_chunks(
            embedding=embedding,
            limit=max(limit * 3, 10),
            distance_threshold=distance_threshold,
            document_ids=document_ids,
        )

        keyword_rows = self.keyword_search_chunks(
            query=query,
            limit=max(limit * 3, 10),
            document_ids=document_ids,
        )

        keywords = self._extract_keywords(query)

        candidates = {}

        for row in semantic_rows:
            chunk_id = row[0]

            candidates[chunk_id] = {
                "row": row,
                "semantic_distance": float(row[4]),
                "keyword_score": 0.0,
            }

        for row in keyword_rows:
            chunk_id = row[0]

            keyword_score = self._keyword_score(
                content=row[3],
                keywords=keywords,
            )

            if chunk_id in candidates:
                candidates[chunk_id]["keyword_score"] = (
                    keyword_score
                )
            else:
                candidates[chunk_id] = {
                    "row": row,
                    "semantic_distance": 1.0,
                    "keyword_score": keyword_score,
                }

        ranked = []

        for candidate in candidates.values():
            semantic_distance = candidate["semantic_distance"]
            keyword_score = candidate["keyword_score"]

            # Convert cosine distance into a similarity score.
            semantic_score = max(
                0.0,
                1.0 - semantic_distance,
            )

            # Hybrid score:
            #
            # 65% semantic relevance
            # 35% lexical relevance
            #
            # Exact technical terms therefore influence
            # ranking without completely overriding semantics.
            hybrid_score = (
                semantic_score * 0.65
                + keyword_score * 0.35
            )

            ranked.append(
                (
                    hybrid_score,
                    candidate["row"],
                )
            )

        ranked.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            row
            for _, row in ranked[:limit]
        ]

    @staticmethod
    def _extract_keywords(query: str) -> list[str]:
        query = query.lower()

        # Fix common typo from natural user input.
        replacements = {
            "scarping": "scraping",
            "scrappng": "scraping",
            "promethues": "prometheus",
        }

        for wrong, correct in replacements.items():
            query = query.replace(
                wrong,
                correct,
            )

        words = re.findall(
            r"[a-zA-Z0-9]+",
            query,
        )

        stop_words = {
            "what",
            "what's",
            "whats",
            "is",
            "are",
            "does",
            "do",
            "did",
            "the",
            "a",
            "an",
            "of",
            "to",
            "in",
            "on",
            "for",
            "with",
            "and",
            "or",
            "how",
            "why",
            "can",
            "could",
            "would",
            "should",
            "use",
            "uses",
            "using",
            "used",
            "tell",
            "me",
            "please",
            "about",
        }

        return [
            word
            for word in words
            if len(word) >= 3
            and word not in stop_words
        ]

    @staticmethod
    def _keyword_score(
        content: str,
        keywords: list[str],
    ) -> float:
        if not keywords:
            return 0.0

        content_lower = content.lower()

        matches = 0

        for keyword in keywords:
            if keyword in content_lower:
                matches += 1

        return matches / len(keywords)