"""Render the textbook knowledge graph as an interactive HTML network.

Usage examples:
    python -m master.data.knowledge.visualize_kg
    python -m master.data.knowledge.visualize_kg --focus "ham so bac hai" --hops 2
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Iterable

import networkx as nx

try:
  from .knowledge_graph import KnowledgeGraph
except ImportError:  # pragma: no cover - allows direct script execution
  from knowledge_graph import KnowledgeGraph


DEFAULT_INPUT = Path(__file__).resolve().parent / "outputs" / "merged_graph_all.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "outputs" / "knowledge_graph.html"

NODE_COLORS = {
    "CONCEPT": "#2E86DE",
    "THEOREM": "#E67E22",
    "FORMULA": "#27AE60",
    "EXAMPLE": "#8E44AD",
}

EDGE_COLORS = {
    "REQUIRES": "#D35400",
    "PART_OF": "#16A085",
    "RELATED_TO": "#7F8C8D",
}


def _neighbor_closure(
    graph: nx.DiGraph,
    seeds: Iterable[str],
    *,
    hops: int,
    max_nodes: int,
) -> set[str]:
    """Collect nearby nodes around seed concepts with bidirectional BFS."""

    selected: set[str] = set()
    frontier: set[str] = set(seeds)
    for seed in frontier:
        if seed in graph:
            selected.add(seed)
        if len(selected) >= max_nodes:
            return selected

    for _ in range(max(0, hops)):
        if not frontier or len(selected) >= max_nodes:
            break

        next_frontier: set[str] = set()
        for node in frontier:
            neighbors = set(graph.successors(node)) | set(graph.predecessors(node))
            for neighbor in neighbors:
                if neighbor in selected:
                    continue
                selected.add(neighbor)
                next_frontier.add(neighbor)
                if len(selected) >= max_nodes:
                    break
            if len(selected) >= max_nodes:
                break
        frontier = next_frontier

    return selected


def _default_subset(graph: nx.DiGraph, max_nodes: int) -> set[str]:
    """Pick high-degree nodes for a readable default preview."""

    ordered = sorted(graph.nodes, key=lambda node_id: graph.degree(node_id), reverse=True)
    return set(ordered[:max_nodes])


def _build_html(nodes_payload: list[dict], edges_payload: list[dict], title: str) -> str:
    """Create a self-contained HTML page using vis-network CDN."""

    nodes_json = json.dumps(nodes_payload, ensure_ascii=False)
    edges_json = json.dumps(edges_payload, ensure_ascii=False)
    safe_title = html.escape(title)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{safe_title}</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    :root {{
      --bg: #f5f7fb;
      --panel: #ffffff;
      --text: #1f2937;
      --subtle: #6b7280;
      --border: #d1d5db;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      gap: 16px;
      min-height: 100vh;
      padding: 16px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      overflow: hidden;
    }}
    #network {{
      width: 100%;
      height: calc(100vh - 32px);
    }}
    .sidebar {{ padding: 16px; }}
    .sidebar h2 {{
      margin-top: 0;
      margin-bottom: 8px;
      font-size: 18px;
    }}
    .meta {{
      color: var(--subtle);
      font-size: 14px;
      line-height: 1.5;
      margin-bottom: 12px;
    }}
    .details {{
      border-top: 1px solid var(--border);
      padding-top: 12px;
      font-size: 14px;
      line-height: 1.55;
      white-space: pre-wrap;
    }}
    .legend {{
      margin-top: 12px;
      border-top: 1px solid var(--border);
      padding-top: 12px;
      font-size: 13px;
      color: var(--subtle);
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }}
    .swatch {{
      width: 10px;
      height: 10px;
      border-radius: 999px;
      border: 1px solid rgba(0, 0, 0, 0.18);
    }}
    @media (max-width: 980px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
      #network {{
        height: 68vh;
      }}
    }}
  </style>
</head>
<body>
  <main class="layout">
    <section class="card">
      <div id="network"></div>
    </section>
    <aside class="card sidebar">
      <h2>Knowledge Graph Viewer</h2>
      <div class="meta">
        Drag to move nodes, scroll to zoom, click a node to inspect details.
      </div>
      <div id="summary" class="meta"></div>
      <div id="details" class="details">Select a node to see metadata.</div>
      <div class="legend">
        <div class="legend-item"><span class="swatch" style="background:#2E86DE"></span> CONCEPT</div>
        <div class="legend-item"><span class="swatch" style="background:#E67E22"></span> THEOREM</div>
        <div class="legend-item"><span class="swatch" style="background:#27AE60"></span> FORMULA</div>
        <div class="legend-item"><span class="swatch" style="background:#8E44AD"></span> EXAMPLE</div>
      </div>
    </aside>
  </main>

  <script>
    const nodesRaw = {nodes_json};
    const edgesRaw = {edges_json};

    const detailsEl = document.getElementById("details");
    const networkEl = document.getElementById("network");
    document.getElementById("summary").textContent =
      `Nodes: ${{nodesRaw.length.toLocaleString()}} | Edges: ${{edgesRaw.length.toLocaleString()}}`;

    const showNodeDetails = (node) => {{
      if (!node) return;
      const lines = [
        `ID: ${{node.id}}`,
        `Label: ${{node.label || ""}}`,
        `Type: ${{node.type || ""}}`,
        `Grade: ${{node.grade ?? "n/a"}}`,
        `Source: ${{node.source_title || "n/a"}}`,
        "",
        `Description: ${{node.description || ""}}`,
      ];
      detailsEl.textContent = lines.join("\n");
    }};

    const renderFallbackSvg = (reason) => {{
      networkEl.innerHTML = "";
      const width = networkEl.clientWidth || 900;
      const height = networkEl.clientHeight || 600;
      const svgNs = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(svgNs, "svg");
      svg.setAttribute("width", "100%");
      svg.setAttribute("height", "100%");
      svg.style.background = "#f8fafc";

      const xs = nodesRaw.map((n) => Number(n.x ?? 0));
      const ys = nodesRaw.map((n) => Number(n.y ?? 0));
      const minX = Math.min(...xs, -1);
      const maxX = Math.max(...xs, 1);
      const minY = Math.min(...ys, -1);
      const maxY = Math.max(...ys, 1);
      const pad = 40;
      const scaleX = (x) => pad + ((x - minX) / (maxX - minX + 1e-9)) * (width - 2 * pad);
      const scaleY = (y) => pad + ((y - minY) / (maxY - minY + 1e-9)) * (height - 2 * pad);

      const byId = new Map(nodesRaw.map((node) => [node.id, node]));

      for (const edge of edgesRaw) {{
        const from = byId.get(edge.from);
        const to = byId.get(edge.to);
        if (!from || !to) continue;
        const line = document.createElementNS(svgNs, "line");
        line.setAttribute("x1", String(scaleX(Number(from.x ?? 0))));
        line.setAttribute("y1", String(scaleY(Number(from.y ?? 0))));
        line.setAttribute("x2", String(scaleX(Number(to.x ?? 0))));
        line.setAttribute("y2", String(scaleY(Number(to.y ?? 0))));
        line.setAttribute("stroke", edge?.color?.color || "#94a3b8");
        line.setAttribute("stroke-opacity", "0.55");
        line.setAttribute("stroke-width", "1.2");
        svg.appendChild(line);
      }}

      for (const node of nodesRaw) {{
        const circle = document.createElementNS(svgNs, "circle");
        circle.setAttribute("cx", String(scaleX(Number(node.x ?? 0))));
        circle.setAttribute("cy", String(scaleY(Number(node.y ?? 0))));
        circle.setAttribute("r", String(Math.max(4, Math.min(12, 2 + Math.sqrt(Number(node.value || 1))))));
        circle.setAttribute("fill", node?.color?.background || "#2E86DE");
        circle.setAttribute("stroke", "#111827");
        circle.setAttribute("stroke-width", "0.8");
        circle.style.cursor = "pointer";
        circle.addEventListener("click", () => showNodeDetails(node));
        svg.appendChild(circle);
      }}

      const note = document.createElement("div");
      note.className = "meta";
      note.textContent = reason
        ? `Fallback mode: ${{reason}}`
        : "Fallback mode: SVG renderer";
      networkEl.appendChild(svg);
      networkEl.appendChild(note);
    }};

    const bootVis = () => {{
      if (typeof vis === "undefined") {{
        renderFallbackSvg("vis-network CDN unavailable");
        return;
      }}

      try {{
        const nodes = new vis.DataSet(nodesRaw);
        const edges = new vis.DataSet(edgesRaw);

        const network = new vis.Network(
          networkEl,
          {{ nodes, edges }},
          {{
            autoResize: true,
            interaction: {{
              hover: true,
              navigationButtons: true,
              multiselect: true,
              tooltipDelay: 120,
            }},
            nodes: {{
              shape: "dot",
              borderWidth: 1,
              font: {{
                face: "Segoe UI, Tahoma, sans-serif",
                size: 13,
              }},
              scaling: {{ min: 8, max: 30 }},
            }},
            edges: {{
              arrows: {{ to: {{ enabled: true, scaleFactor: 0.55 }} }},
              width: 1.2,
              smooth: {{ type: "continuous" }},
            }},
            physics: {{
              enabled: true,
              stabilization: {{ iterations: 220 }},
              forceAtlas2Based: {{
                gravitationalConstant: -50,
                centralGravity: 0.01,
                springLength: 120,
                springConstant: 0.08,
              }},
              solver: "forceAtlas2Based",
            }},
          }}
        );

        network.on("selectNode", (params) => {{
          const node = nodes.get(params.nodes[0]);
          showNodeDetails(node);
        }});

        network.on("deselectNode", () => {{
          detailsEl.textContent = "Select a node to see metadata.";
        }});
      }} catch (error) {{
        console.error("Knowledge graph render error:", error);
        renderFallbackSvg(error?.message || "runtime error");
      }}
    }};

    bootVis();
  </script>
</body>
</html>
"""


def build_visualization(
    input_path: Path,
    output_path: Path,
    *,
    focus: str | None,
    hops: int,
    max_nodes: int,
) -> tuple[int, int, str | None]:
    """Generate HTML payload from graph JSON and return summary stats."""

    kg = KnowledgeGraph()
    kg.load_from_file(input_path)
    graph = kg.graph

    selected_nodes: set[str]
    resolved_focus: str | None = None
    if focus:
        resolved_focus = kg.resolve_concept_id(focus)
        if not resolved_focus:
            raise ValueError(
                f"Cannot resolve focus concept: {focus!r}. "
                "Try using exact id or a clearer label."
            )
        selected_nodes = _neighbor_closure(
            graph,
            [resolved_focus],
            hops=hops,
            max_nodes=max_nodes,
        )
    else:
        selected_nodes = _default_subset(graph, max_nodes=max_nodes)

    subgraph = graph.subgraph(selected_nodes).copy()
    layout = nx.spring_layout(subgraph.to_undirected(), seed=42, iterations=120)

    node_payload: list[dict] = []
    for node_id in selected_nodes:
        node_data = graph.nodes[node_id]
        label = node_data.get("label") or node_id
        node_type = node_data.get("type") or "CONCEPT"
        degree = graph.in_degree(node_id) + graph.out_degree(node_id)
        x, y = layout.get(node_id, (0.0, 0.0))
        node_payload.append(
            {
                "id": node_id,
                "label": label,
                "type": node_type,
                "description": node_data.get("description"),
                "grade": node_data.get("grade"),
                "source_title": node_data.get("source_title"),
                "value": max(2, degree),
          "x": float(x),
          "y": float(y),
                "color": {
                    "background": NODE_COLORS.get(node_type, "#2980B9"),
                    "border": "#1f2937",
                    "highlight": {"background": "#111827", "border": "#111827"},
                },
                "title": (
                    f"{html.escape(label)}"
                    f"<br><b>{html.escape(node_id)}</b>"
                    f"<br>type: {html.escape(str(node_type))}"
                ),
            }
        )

    edge_payload: list[dict] = []
    for source, target, data in graph.edges(data=True):
        if source not in selected_nodes or target not in selected_nodes:
            continue
        relation = data.get("relation", "RELATED_TO")
        edge_payload.append(
            {
                "from": source,
                "to": target,
                "label": relation,
                "color": {"color": EDGE_COLORS.get(relation, "#7F8C8D")},
                "font": {"size": 11, "align": "top"},
                "arrows": "to",
                "title": data.get("rationale") or relation,
            }
        )

    html_doc = _build_html(
        node_payload,
        edge_payload,
        title="MASTER Knowledge Graph Viewer",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_doc, encoding="utf-8")
    return len(node_payload), len(edge_payload), resolved_focus


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render an interactive HTML view of the textbook knowledge graph."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to merged graph JSON (default: outputs/merged_graph_all.json).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output HTML path.",
    )
    parser.add_argument(
        "--focus",
        type=str,
        default=None,
        help="Optional concept id or label to center the visualization around.",
    )
    parser.add_argument(
        "--hops",
        type=int,
        default=2,
        help="Neighborhood hop count when --focus is set.",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=250,
        help="Maximum number of nodes to render.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_nodes <= 0:
        raise ValueError("--max-nodes must be greater than 0")

    node_count, edge_count, resolved_focus = build_visualization(
        args.input,
        args.output,
        focus=args.focus,
        hops=args.hops,
        max_nodes=args.max_nodes,
    )
    focus_msg = f" | focus={resolved_focus}" if resolved_focus else ""
    print(
        f"Generated graph view at {args.output} "
        f"(nodes={node_count}, edges={edge_count}{focus_msg})."
    )


if __name__ == "__main__":
    main()