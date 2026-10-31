import { useState, useMemo, useRef, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import ForceGraph2D from "react-force-graph-2d";
import { useQuery } from "@tanstack/react-query";
import { fetchGraphStats, fetchPaperGraph } from "../api/graph";
import { fetchPapers } from "../api/papers";
import { GraphStatsResponse, PaperGraphResponse, PaperListResponse } from "../types/api";
import { NodeDetailsPanel } from "../components/graph/NodeDetailsPanel";
import { CanonicalizationTab } from "../components/graph/CanonicalizationTab";
import { LinkPredictionTab } from "../components/graph/LinkPredictionTab";
import { Button } from "../components/ui/Button";
import { Search, Filter, ZoomIn, ZoomOut, RefreshCw, Network, GitMerge, Brain } from "lucide-react";

export function KnowledgeGraphPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialSearch = searchParams.get("search") || "";

  const [activeTab, setActiveTab] = useState<"visualizer" | "canonicalize" | "prediction">("visualizer");
  const [selectedPaperId, setSelectedPaperId] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState(initialSearch);
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const fgRef = useRef<any>(null);

  // Fetch papers for selector
  const { data: papersData } = useQuery<PaperListResponse>({
    queryKey: ["papers-list"],
    queryFn: () => fetchPapers(0, 100),
  });

  // Fetch Global Graph Stats
  const { data: statsData } = useQuery<GraphStatsResponse>({
    queryKey: ["graph-stats"],
    queryFn: fetchGraphStats,
  });

  // Fetch Paper Graph
  const activePaperId = selectedPaperId || (papersData?.papers?.[0]?.id ?? "");
  const { data: paperGraph, isLoading, refetch } = useQuery<PaperGraphResponse>({
    queryKey: ["paper-graph-active", activePaperId],
    queryFn: () => fetchPaperGraph(activePaperId),
    enabled: Boolean(activePaperId),
  });

  // Color mapping by entity type
  const entityColors: Record<string, string> = {
    CONCEPT: "#3A3531",
    METHOD: "#1D3557",
    DATASET: "#704214",
    MODEL: "#1C4B27",
    AUTHOR: "#432874",
    TASK: "#6B5C4D",
    METRIC: "#7A1C1C",
    DEFAULT: "#635D59",
  };

  // Build nodes and links for ForceGraph
  const graphData = useMemo(() => {
    if (!paperGraph || !paperGraph.nodes || paperGraph.nodes.length === 0) {
      return { nodes: [], links: [] };
    }

    const filteredNodes = paperGraph.nodes
      .filter((n) => {
        const matchesType = selectedType === "ALL" || n.type === selectedType;
        const matchesSearch =
          !searchQuery.trim() ||
          n.name.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesType && matchesSearch;
      })
      .map((n) => ({
        id: n.name,
        name: n.name,
        type: n.type,
        val: 10,
        description: n.description,
      }));

    const validNodeIds = new Set(filteredNodes.map((n) => n.id));

    const filteredLinks = paperGraph.edges
      .filter((e) => validNodeIds.has(e.source) && validNodeIds.has(e.target))
      .map((e) => ({
        source: e.source,
        target: e.target,
        label: e.relation_type,
        description: e.description,
      }));

    return { nodes: filteredNodes, links: filteredLinks };
  }, [paperGraph, selectedType, searchQuery]);

  // Center on node if search param matched
  useEffect(() => {
    if (initialSearch && fgRef.current && graphData.nodes.length > 0) {
      const match = graphData.nodes.find(
        (n) => n.name.toLowerCase() === initialSearch.toLowerCase()
      );
      if (match) {
        setSelectedNode(match);
      }
    }
  }, [initialSearch, graphData]);

  const handleNodeClick = (node: any) => {
    // Find neighbors
    const neighbors = graphData.links
      .filter((l: any) => {
        const s = typeof l.source === "object" ? (l.source as any).id : l.source;
        const t = typeof l.target === "object" ? (l.target as any).id : l.target;
        return s === node.id || t === node.id;
      })
      .map((l: any) => {
        const s = typeof l.source === "object" ? (l.source as any).id : l.source;
        const t = typeof l.target === "object" ? (l.target as any).id : l.target;
        return s === node.id ? t : s;
      });

    setSelectedNode({ ...node, neighbors });
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 800);
      fgRef.current.zoom(2.5, 800);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden font-serif bg-parchment-surface dark:bg-darkpaper-surface">
      {/* Top Bar: Navigation Tabs & Stats */}
      <div className="border-b border-parchment-outline-variant px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 bg-parchment-container-low dark:bg-darkpaper-container">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("visualizer")}
            className={`px-3 py-1 text-xs font-serif flex items-center gap-1.5 border transition-colors ${
              activeTab === "visualizer"
                ? "bg-parchment-primary text-parchment-on-primary border-parchment-primary dark:bg-darkpaper-primary dark:text-darkpaper-on-primary"
                : "border-parchment-outline-variant hover:bg-parchment-container"
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>Interactive Graph Canvas</span>
          </button>

          <button
            onClick={() => setActiveTab("canonicalize")}
            className={`px-3 py-1 text-xs font-serif flex items-center gap-1.5 border transition-colors ${
              activeTab === "canonicalize"
                ? "bg-parchment-primary text-parchment-on-primary border-parchment-primary dark:bg-darkpaper-primary dark:text-darkpaper-on-primary"
                : "border-parchment-outline-variant hover:bg-parchment-container"
            }`}
          >
            <GitMerge className="w-3.5 h-3.5" />
            <span>Entity Canonicalization</span>
          </button>

          <button
            onClick={() => setActiveTab("prediction")}
            className={`px-3 py-1 text-xs font-serif flex items-center gap-1.5 border transition-colors ${
              activeTab === "prediction"
                ? "bg-parchment-primary text-parchment-on-primary border-parchment-primary dark:bg-darkpaper-primary dark:text-darkpaper-on-primary"
                : "border-parchment-outline-variant hover:bg-parchment-container"
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            <span>GNN Link Prediction</span>
          </button>
        </div>

        {/* Global DB Stats Badges */}
        {statsData && (
          <div className="hidden lg:flex items-center gap-3 text-[11px] font-mono text-parchment-secondary">
            <span>Neo4j Nodes: <strong className="text-parchment-primary">{statsData.total_nodes}</strong></span>
            <span>•</span>
            <span>Triples: <strong className="text-parchment-primary">{statsData.total_relationships}</strong></span>
          </div>
        )}
      </div>

      {activeTab === "visualizer" && (
        <div className="flex-1 flex flex-col relative overflow-hidden">
          {/* Visualizer Filter Controls Overlay */}
          <div className="p-3 border-b border-parchment-outline-variant bg-parchment-container-lowest/90 dark:bg-darkpaper-container-low/90 backdrop-blur-xs flex flex-wrap items-center justify-between gap-3 z-10 text-xs">
            <div className="flex items-center gap-2 flex-wrap">
              {/* Paper Selector */}
              <select
                value={selectedPaperId}
                onChange={(e) => setSelectedPaperId(e.target.value)}
                className="p-1.5 bg-parchment-container border border-parchment-outline-variant text-xs font-serif outline-none"
              >
                <option value="">Select Paper Subnetwork...</option>
                {papersData?.papers?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title || p.filename}
                  </option>
                ))}
              </select>

              {/* Type Filter */}
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="p-1.5 bg-parchment-container border border-parchment-outline-variant text-xs font-serif outline-none uppercase font-mono text-[11px]"
              >
                <option value="ALL">All Entity Types</option>
                <option value="CONCEPT">Concepts</option>
                <option value="METHOD">Methods</option>
                <option value="DATASET">Datasets</option>
                <option value="MODEL">Models</option>
                <option value="AUTHOR">Authors</option>
                <option value="METRIC">Metrics</option>
              </select>

              {/* Search in Graph */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2 top-2 text-parchment-secondary" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter nodes..."
                  className="pl-7 pr-2 py-1 text-xs font-serif bg-parchment-container border border-parchment-outline-variant outline-none focus:border-parchment-primary w-40"
                />
              </div>
            </div>

            {/* Zoom Controls */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => fgRef.current?.zoom(fgRef.current.zoom() * 1.3, 400)}
                className="p-1.5 border border-parchment-outline-variant hover:bg-parchment-container"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => fgRef.current?.zoom(fgRef.current.zoom() / 1.3, 400)}
                className="p-1.5 border border-parchment-outline-variant hover:bg-parchment-container"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => {
                  refetch();
                  fgRef.current?.zoomToFit(400);
                }}
                className="p-1.5 border border-parchment-outline-variant hover:bg-parchment-container"
                title="Reset View"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Graph 2D Canvas */}
          <div className="flex-1 w-full h-full relative bg-[#fcf8f0] dark:bg-[#151311]">
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              nodeLabel={(node: any) => `${node.name} (${node.type})`}
              nodeColor={(node: any) => entityColors[node.type] || entityColors.DEFAULT}
              nodeRelSize={6}
              linkColor={() => "#cfc5bd"}
              linkDirectionalArrowLength={4}
              linkDirectionalArrowRelPos={1}
              linkLabel={(link: any) => link.label}
              onNodeClick={handleNodeClick}
              cooldownTicks={120}
              d3VelocityDecay={0.3}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                const label = node.name;
                const fontSize = 12 / globalScale;
                ctx.font = `${fontSize}px 'Newsreader', serif`;
                const textWidth = ctx.measureText(label).width;
                const bckgDimensions = [textWidth, fontSize].map((n) => n + fontSize * 0.4);

                // Draw circle node
                ctx.beginPath();
                ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI, false);
                ctx.fillStyle = entityColors[node.type] || "#3A3531";
                ctx.fill();
                ctx.lineWidth = 1.5;
                ctx.strokeStyle = "#ffffff";
                ctx.stroke();

                // Draw label
                if (globalScale > 0.8) {
                  ctx.fillStyle = "rgba(254, 249, 240, 0.85)";
                  ctx.fillRect(
                    node.x - bckgDimensions[0] / 2,
                    node.y + 7,
                    bckgDimensions[0],
                    bckgDimensions[1]
                  );
                  ctx.textAlign = "center";
                  ctx.textBaseline = "middle";
                  ctx.fillStyle = "#1d1c16";
                  ctx.fillText(label, node.x, node.y + 7 + bckgDimensions[1] / 2);
                }
              }}
            />

            {/* Empty State when no nodes exist */}
            {graphData.nodes.length === 0 && (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center select-none bg-parchment-surface/85 dark:bg-darkpaper-surface/85 backdrop-blur-xs z-10">
                <div className="w-12 h-12 mb-3 flex items-center justify-center border border-dashed border-parchment-outline-variant bg-parchment-container text-parchment-secondary">
                  <Network className="w-5 h-5 opacity-60" />
                </div>
                <h3 className="font-serif text-lg font-medium text-parchment-primary dark:text-darkpaper-primary mb-1">
                  No Knowledge Graph Entities Extracted Yet
                </h3>
                <p className="font-serif text-xs text-parchment-secondary max-w-sm mb-4 leading-relaxed">
                  The Neo4j graph is currently empty. Upload research PDFs in the Research Papers section to automatically extract entities, concepts, and relationships.
                </p>
                <button
                  onClick={() => navigate("/papers")}
                  className="px-4 py-2 bg-parchment-primary text-parchment-on-primary hover:bg-parchment-primary-container text-xs font-serif transition-colors cursor-pointer"
                >
                  Go to Research Papers →
                </button>
              </div>
            )}

            {/* Legend Overlay */}
            {graphData.nodes.length > 0 && (
              <div className="absolute bottom-4 left-4 p-3 bg-parchment-container-lowest/90 dark:bg-darkpaper-surface/90 border border-parchment-outline-variant text-[11px] font-mono pointer-events-none select-none">
                <span className="text-[10px] uppercase text-parchment-secondary block mb-1">
                  Entity Types
                </span>
                <div className="grid grid-cols-2 gap-x-3 gap-y-1">
                  {Object.entries(entityColors)
                    .filter(([k]) => k !== "DEFAULT")
                    .map(([type, color]) => (
                      <div key={type} className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 inline-block" style={{ backgroundColor: color }} />
                        <span className="text-parchment-on-surface">{type}</span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Selected Node Details Drawer */}
            <NodeDetailsPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
          </div>
        </div>
      )}

      {activeTab === "canonicalize" && (
        <div className="flex-1 overflow-y-auto">
          <CanonicalizationTab />
        </div>
      )}

      {activeTab === "prediction" && (
        <div className="flex-1 overflow-y-auto">
          <LinkPredictionTab />
        </div>
      )}
    </div>
  );
}
