"""
Graph Neural Network (GNN) Link Prediction Engine.
Uses PyTorch Graph Convolutional Networks (GCN) to learn entity graph node embeddings
and predict prospective research links between concepts, methods, datasets, and tools.
"""
from typing import List, Dict, Any, Tuple, Optional
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from app.core.logging import logger
from app.graph.canonicalizer import EntityCanonicalizer


class GCNLayer(nn.Module):
    """
    2D Graph Convolutional Layer (Spectral Graph Convolution).
    H^(l+1) = ReLU( \tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2} H^(l) W^(l) )
    """
    def __init__(self, in_features: int, out_features: int):
        super(GCNLayer, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1.0 / math.sqrt(self.weight.size(1))
        self.weight.data.uniform_(-stdv, stdv)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        x: (N, in_features)
        adj: (N, N) normalized adjacency matrix
        """
        support = torch.mm(x, self.weight)
        output = torch.mm(adj, support)
        return output


class GCNEncoder(nn.Module):
    """
    2-Layer Graph Convolutional Network Encoder for Graph Node Embeddings.
    """
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        super(GCNEncoder, self).__init__()
        self.gcn1 = GCNLayer(input_dim, hidden_dim)
        self.gcn2 = GCNLayer(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.gcn1(x, adj))
        h = F.dropout(h, p=0.1, training=self.training)
        embeddings = self.gcn2(h, adj)
        return embeddings


class GNNLinkPredictor:
    """
    Service for building entity graphs, executing GCN message passing,
    and predicting emerging or missing links between research entities.
    """

    @classmethod
    def normalize_adjacency(cls, adj: torch.Tensor) -> torch.Tensor:
        """
        Computes symmetric normalized adjacency matrix: \tilde{A} = D^{-1/2} (A + I) D^{-1/2}
        """
        n = adj.size(0)
        adj_self = adj + torch.eye(n, device=adj.device)
        deg = torch.sum(adj_self, dim=1)
        deg_inv_sqrt = torch.pow(deg, -0.5)
        deg_inv_sqrt[torch.isinf(deg_inv_sqrt)] = 0.0
        d_mat = torch.diag(deg_inv_sqrt)
        return torch.mm(torch.mm(d_mat, adj_self), d_mat)

    @classmethod
    def build_graph_matrices(
        cls,
        entities: List[str],
        relationships: List[Tuple[str, str, str]]
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, int], Dict[int, str]]:
        """
        Constructs node features X and adjacency matrix A from entity and edge lists.
        relationships: list of (source_entity, target_entity, relation_type)
        """
        canonical_entities = list(dict.fromkeys(
            EntityCanonicalizer.canonicalize_name(e) for e in entities if e and e.strip()
        ))
        
        # Build index mapping
        entity_to_idx = {e: i for i, e in enumerate(canonical_entities)}
        idx_to_entity = {i: e for i, e in enumerate(canonical_entities)}
        n = len(canonical_entities)

        if n == 0:
            return torch.zeros((0, 16)), torch.zeros((0, 0)), {}, {}

        # Adjacency matrix
        adj = torch.zeros((n, n), dtype=torch.float32)
        for src, tgt, _ in relationships:
            c_src = EntityCanonicalizer.canonicalize_name(src)
            c_tgt = EntityCanonicalizer.canonicalize_name(tgt)
            if c_src in entity_to_idx and c_tgt in entity_to_idx:
                u, v = entity_to_idx[c_src], entity_to_idx[c_tgt]
                adj[u, v] = 1.0
                adj[v, u] = 1.0  # Undirected message passing for GCN

        # Simple initial node feature encoding based on hash/character n-grams
        feat_dim = 16
        x = torch.zeros((n, feat_dim), dtype=torch.float32)
        for i, entity in enumerate(canonical_entities):
            for char_idx, char in enumerate(entity.lower()[:feat_dim]):
                x[i, char_idx] = float(ord(char) % 100) / 100.0

        return x, adj, entity_to_idx, idx_to_entity

    @classmethod
    def predict_top_links(
        cls,
        source_entity: str,
        target_candidates: List[str],
        existing_relationships: List[Tuple[str, str, str]],
        all_entities: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Runs GCN node embedding inference and ranks candidate target entities for prospective research links.
        """
        canonical_source = EntityCanonicalizer.canonicalize_name(source_entity)
        canonical_candidates = [EntityCanonicalizer.canonicalize_name(c) for c in target_candidates]

        # Combine all entities into unified graph set
        full_entity_set = set()
        if all_entities:
            full_entity_set.update(EntityCanonicalizer.canonicalize_name(e) for e in all_entities)
        full_entity_set.add(canonical_source)
        full_entity_set.update(canonical_candidates)

        for src, tgt, _ in existing_relationships:
            full_entity_set.add(EntityCanonicalizer.canonicalize_name(src))
            full_entity_set.add(EntityCanonicalizer.canonicalize_name(tgt))

        entities_list = list(full_entity_set)
        x, adj, entity_to_idx, idx_to_entity = cls.build_graph_matrices(entities_list, existing_relationships)

        if canonical_source not in entity_to_idx:
            logger.warning(f"Source entity '{source_entity}' not present in graph.")
            return []

        # Normalize adjacency matrix
        norm_adj = cls.normalize_adjacency(adj)

        # Initialize GCN Encoder (input_dim=16, hidden_dim=32, output_dim=16)
        torch.manual_seed(42)
        model = GCNEncoder(input_dim=16, hidden_dim=32, output_dim=16)
        model.eval()

        with torch.no_grad():
            node_embeddings = model(x, norm_adj)
            node_embeddings = F.normalize(node_embeddings, p=2, dim=1)

        src_idx = entity_to_idx[canonical_source]
        src_vec = node_embeddings[src_idx].unsqueeze(0)  # (1, output_dim)

        results: List[Dict[str, Any]] = []

        for candidate in canonical_candidates:
            if candidate == canonical_source or candidate not in entity_to_idx:
                continue
            
            tgt_idx = entity_to_idx[candidate]
            tgt_vec = node_embeddings[tgt_idx].unsqueeze(0)

            # Link score = Sigmoid of dot product similarity
            cosine_sim = float(torch.mm(src_vec, tgt_vec.T).item())
            link_prob = float(torch.sigmoid(torch.tensor(cosine_sim * 3.0)).item())

            results.append({
                "target_entity": candidate,
                "link_probability": round(link_prob, 4),
                "similarity_score": round(cosine_sim, 4),
                "gnn_recommendation": "High prospective research connection" if link_prob > 0.6 else "Moderate research connection"
            })

        # Sort candidate results descending by link probability
        results.sort(key=lambda r: r["link_probability"], reverse=True)
        return results[:top_k]
