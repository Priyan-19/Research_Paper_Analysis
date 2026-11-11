import re
from typing import List, Dict, Any, Optional

from app.core.logging import logger
from app.schemas.rag import CitationBadge


class CitationGuard:
    """
    Citation Extractor and Evidence Grounding Guardrail Service.
    Parses inline citation tags from LLM answers and evaluates context sufficiency thresholds.
    """

    INSUFFICIENT_EVIDENCE_PHRASE = "there is insufficient evidence to answer this question"

    @classmethod
    def extract_citation_badges(
        cls,
        answer_text: str,
        retrieved_sources: List[Dict[str, Any]]
    ) -> List[CitationBadge]:
        """
        Parses inline citation tags ([Paper X, Page Y], [Source N], [Evidence Item #N], [Graph: ...])
        from generated LLM text and resolves them against retrieved source metadata.
        """
        if not answer_text or not retrieved_sources or not answer_text.strip():
            return []

        badges: List[CitationBadge] = []
        seen_keys = set()

        # Build lookup maps for rapid source resolving (by paper_id, by paper_title, and by 1-based index)
        paper_lookup: Dict[str, Dict[str, Any]] = {}
        index_map: Dict[int, Dict[str, Any]] = {}

        for idx, src in enumerate(retrieved_sources, start=1):
            pid = str(src.get("paper_id", "")).strip()
            title = str(src.get("paper_title", "")).strip()
            if pid:
                paper_lookup[pid.lower()] = src
            if title:
                paper_lookup[title.lower()] = src
            index_map[idx] = src

        # Pattern 1: [Paper: <title_or_id>, Page: <page_num>] or [Paper <title_or_id>]
        pattern_paper_page = re.findall(
            r'\[Paper:?\s*(.*?)(?:,\s*Page:?\s*(\d+))?(?:,\s*Section:?\s*([^\]]+))?\]',
            answer_text,
            re.IGNORECASE
        )
        for match in pattern_paper_page:
            pid, page_str, sec_str = match
            pid_clean = pid.strip()
            if not pid_clean:
                continue
            page_num = int(page_str) if page_str else None
            sec_name = sec_str.strip() if sec_str else None

            # Resolve against lookup
            source_meta = paper_lookup.get(pid_clean.lower())
            if not source_meta:
                for key, val in paper_lookup.items():
                    if key in pid_clean.lower() or pid_clean.lower() in key:
                        source_meta = val
                        break

            source_meta = source_meta or {}
            real_pid = source_meta.get("paper_id") or pid_clean
            title = source_meta.get("paper_title") or source_meta.get("title") or pid_clean
            page = page_num or source_meta.get("page_number")
            sec = sec_name or source_meta.get("section_name")
            snippet = source_meta.get("text") or source_meta.get("snippet")

            tag_str = f"[Paper: {pid_clean}"
            if page:
                tag_str += f", Page: {page}"
            tag_str += "]"

            dedup_key = f"{real_pid}_{page}_{sec}".lower()
            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                badges.append(
                    CitationBadge(
                        paper_id=real_pid,
                        paper_title=title,
                        page_number=page,
                        section_name=sec,
                        citation_tag=tag_str,
                        snippet=snippet[:300] if snippet else None,
                        source_type=source_meta.get("source_type", "hybrid"),
                        relationship=source_meta.get("relationship"),
                        source_entity=source_meta.get("source_entity"),
                        target_entity=source_meta.get("target_entity"),
                        score=source_meta.get("score")
                    )
                )

        # Pattern 2: [Source N] or [Evidence Item #N] or [Evidence Item N] or [Evidence N]
        pattern_source_idx = re.findall(
            r'\[(?:Source|Evidence\s*Item|Evidence)\s*#?:?\s*(\d+)\]',
            answer_text,
            re.IGNORECASE
        )
        for idx_str in pattern_source_idx:
            idx = int(idx_str)
            if idx in index_map:
                src = index_map[idx]
                pid = str(src.get("paper_id", f"source_{idx}")).strip()
                title = src.get("paper_title") or src.get("title") or pid
                page = src.get("page_number")
                sec = src.get("section_name")
                snippet = src.get("text") or src.get("snippet")

                tag_str = f"[Source {idx}]"
                dedup_key = f"source_{idx}_{pid}".lower()
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    badges.append(
                        CitationBadge(
                            paper_id=pid,
                            paper_title=title,
                            page_number=page,
                            section_name=sec,
                            citation_tag=tag_str,
                            snippet=snippet[:300] if snippet else None,
                            source_type=src.get("source_type", "hybrid"),
                            relationship=src.get("relationship"),
                            source_entity=src.get("source_entity"),
                            target_entity=src.get("target_entity"),
                            score=src.get("score")
                        )
                    )

        # Pattern 3: [Graph: (A) -> [REL] -> (B)] or [Graph: A REL B]
        pattern_graph = re.findall(r'\[Graph:?\s*([^\]]+)\]', answer_text, re.IGNORECASE)
        for g_match in pattern_graph:
            g_str = g_match.strip()
            tag_str = f"[Graph: {g_str}]"
            if tag_str.lower() not in seen_keys:
                seen_keys.add(tag_str.lower())
                matched_src = next(
                    (s for s in retrieved_sources if s.get("source_type") == "graph" and (s.get("relationship") or "") in g_str),
                    None
                )
                badges.append(
                    CitationBadge(
                        paper_id=matched_src.get("paper_id", "graph_rel") if matched_src else "graph_rel",
                        paper_title=matched_src.get("paper_title", "Knowledge Graph Network") if matched_src else "Knowledge Graph Network",
                        page_number=None,
                        section_name="Knowledge Graph",
                        citation_tag=tag_str,
                        snippet=f"Neo4j Knowledge Relation: {g_str}",
                        source_type="graph",
                        relationship=matched_src.get("relationship") if matched_src else g_str,
                        source_entity=matched_src.get("source_entity") if matched_src else None,
                        target_entity=matched_src.get("target_entity") if matched_src else None,
                        score=matched_src.get("score") if matched_src else None
                    )
                )

        return badges

    @classmethod
    def is_insufficient_evidence(
        cls,
        answer_text: str,
        retrieved_items: List[Any],
        score_threshold: float = 0.05
    ) -> bool:
        """
        Evaluates whether context is insufficient or if the LLM explicitly declared insufficient evidence.
        """
        # 1. No evidence retrieved at all
        if not retrieved_items:
            return True

        # 2. Check if answer text explicitly contains the insufficient evidence phrase
        if answer_text and cls.INSUFFICIENT_EVIDENCE_PHRASE.lower() in answer_text.lower():
            return True

        return False

    @classmethod
    def get_insufficient_evidence_message(cls, query: str) -> str:
        """
        Returns a standardized, evidence-grounded fallback response.
        """
        return (
            f"Based on the analyzed research papers, there is insufficient evidence to answer "
            f"the question: '{query}'. Please upload additional relevant PDFs or refine your search parameters."
        )

    @classmethod
    def replace_paper_ids_with_titles(
        cls,
        answer_text: str,
        retrieved_sources: List[Dict[str, Any]]
    ) -> str:
        """
        Replaces raw UUID paper IDs in generated LLM answer text with clean paper titles.
        Example: [Paper: bdb7a170-b3b0-49dd-be3e-d1d4bf61b27e, Page: 3] -> [Paper: LangChain Paper, Page: 3]
        """
        if not answer_text or not retrieved_sources:
            return answer_text

        cleaned_text = answer_text
        for src in retrieved_sources:
            pid = str(src.get("paper_id", "")).strip()
            title = str(src.get("paper_title", "")).strip()
            if pid and title and pid.lower() != title.lower():
                cleaned_text = cleaned_text.replace(pid, title)

        return cleaned_text
