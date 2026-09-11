"""
Standalone script for GNN Link Prediction Experimentation & Benchmark.
Usage:
    python -m scripts.gnn_link_prediction
"""
from typing import List, Tuple
from app.graph.gnn_link_predictor import GNNLinkPredictor
from app.core.logging import logger


def main():
    logger.info("=== Running GNN Link Prediction Experiment ===")

    source_entity = "Retrieval Augmented Generation"
    target_candidates = [
        "Graph Neural Networks",
        "Transformer",
        "PostgreSQL",
        "Sentence Transformers",
        "ReactJS"
    ]

    existing_relationships: List[Tuple[str, str, str]] = [
        ("Retrieval Augmented Generation", "Sentence Transformers", "USES_METHOD"),
        ("Sentence Transformers", "Transformer", "EXTENDS"),
        ("Graph Neural Networks", "Transformer", "APPLIES_TO"),
        ("PostgreSQL", "Retrieval Augmented Generation", "USES_METHOD")
    ]

    print(f"\n[GNN Link Predictor] Target Source Entity: '{source_entity}'")
    print(f"[GNN Link Predictor] Evaluating {len(target_candidates)} Target Candidates...\n")

    predictions = GNNLinkPredictor.predict_top_links(
        source_entity=source_entity,
        target_candidates=target_candidates,
        existing_relationships=existing_relationships,
        top_k=5
    )

    print(f"{'Rank':<5} | {'Target Entity':<25} | {'Probability':<12} | {'Similarity':<12} | {'Recommendation':<30}")
    print("-" * 90)

    for idx, item in enumerate(predictions, start=1):
        print(f"{idx:<5} | {item['target_entity']:<25} | {item['link_probability']:<12.4f} | {item['similarity_score']:<12.4f} | {item['gnn_recommendation']:<30}")

    print("\n=== GNN Link Prediction Experiment Completed Successfully ===")


if __name__ == "__main__":
    main()
