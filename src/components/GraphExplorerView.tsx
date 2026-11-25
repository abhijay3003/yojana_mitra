import React, { useEffect, useState } from 'react';
import { GitBranch, Loader2, Search } from 'lucide-react';
import type { GraphEdgeView, GraphNodeView, Scheme } from '../lib/types';

interface Props {
  schemes: Scheme[];
}

interface GraphResult {
  relation: string;
  matchedSchemes: Scheme[];
  paths: string[];
  nodes: GraphNodeView[];
  edges: GraphEdgeView[];
}

const MULTIHOP_PRESETS = [
  {
    label: 'Rythu Bandhu Supersedes + Complements',
    query: 'Which scheme superseded Telangana Rythu Bandhu and what schemes complement it?',
    anchor: 'TS_RYTHU_BANDHU_LEGACY',
  },
  {
    label: 'Rythu Bharosa Complementary Stack',
    query: 'Which schemes complement Telangana Rythu Bharosa for farmers?',
    anchor: 'TS_RYTHU_BHAROSA',
  },
  {
    label: 'Shared White Ration Card Schemes',
    query: 'Which Telangana schemes share the White Ration Card document?',
    anchor: 'TS_MAHALAKSHMI',
  },
  {
    label: 'Indiramma Housing Conflicts',
    query: 'Which housing schemes are mutually exclusive with Indiramma Indlu?',
    anchor: 'TS_INDIRAMMA_INDLU',
  },
  {
    label: 'Karnataka Gruha Lakshmi Stack',
    query: 'Which schemes complement Karnataka Gruha Lakshmi?',
    anchor: 'KA_GRUHA_LAKSHMI',
  },
];

const NODE_COLORS: Record<string, { fill: string; stroke: string; text: string }> = {
  Scheme: { fill: '#EFF6FF', stroke: '#1D4ED8', text: '#1E3A8A' },
  State: { fill: '#F0FDF4', stroke: '#15803D', text: '#14532D' },
  Ministry: { fill: '#F8FAFC', stroke: '#475569', text: '#1E293B' },
  Document: { fill: '#FFFBEB', stroke: '#B45309', text: '#78350F' },
  Benefit: { fill: '#ECFDF5', stroke: '#047857', text: '#064E3B' },
  BeneficiaryCategory: { fill: '#F5F3FF', stroke: '#6D28D9', text: '#4C1D95' },
};

export const GraphExplorerView: React.FC<Props> = ({ schemes }) => {
  const [query, setQuery] = useState(MULTIHOP_PRESETS[0].query);
  const [anchor, setAnchor] = useState<string | undefined>(MULTIHOP_PRESETS[0].anchor);
  const [result, setResult] = useState<GraphResult | null>(null);
  const [loading, setLoading] = useState(false);

  const runQuery = async (q: string, anchorId?: string) => {
    setLoading(true);
    try {
      const res = await fetch('/api/graph/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, anchorSchemeId: anchorId }),
      });
      if (res.ok) {
        setResult((await res.json()) as GraphResult);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void runQuery(MULTIHOP_PRESETS[0].query, MULTIHOP_PRESETS[0].anchor);
  }, []);

  // Compute radial SVG coordinates for clean readable node graph
  const svgWidth = 760;
  const svgHeight = 400;
  const cx = svgWidth / 2;
  const cy = svgHeight / 2;
  const positioned = new Map<string, { x: number; y: number; node: GraphNodeView }>();

  if (result && result.nodes.length > 0) {
    const first = result.nodes[0];
    positioned.set(first.id, { x: cx, y: cy, node: first });
    const rest = result.nodes.slice(1, 13);
    const radiusX = 270;
    const radiusY = 148;
    rest.forEach((node, idx) => {
      const angle = (2 * Math.PI * idx) / Math.max(rest.length, 1) - Math.PI / 2;
      positioned.set(node.id, {
        x: cx + Math.cos(angle) * radiusX,
        y: cy + Math.sin(angle) * radiusY,
        node,
      });
    });
  }

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h2 className="text-lg font-bold text-slate-900">Welfare Knowledge GraphRAG (P5)</h2>
        <p className="text-xs text-slate-500">
          Multi-hop relational reasoning across {schemes.length} schemes, ministries, states, shared documents, supersedes, and mutual-exclusion edges.
        </p>
      </div>

      {/* Presets + Query Bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
        <div className="flex flex-wrap gap-2">
          {MULTIHOP_PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => {
                setQuery(p.query);
                setAnchor(p.anchor);
                void runQuery(p.query, p.anchor);
              }}
              className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-800 transition-colors"
            >
              {p.label}
            </button>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            setAnchor(undefined);
            void runQuery(query, undefined);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a multi-hop question (complementary schemes, superseded rules, shared documents)..."
            className="flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-700 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-800 transition-colors whitespace-nowrap shrink-0"
          >
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
            Traverse Graph
          </button>
        </form>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
        {/* Interactive SVG Graph */}
        <div className="lg:col-span-8 rounded-xl border border-slate-200 bg-white p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
            <span className="font-semibold text-slate-800">
              Active Relation: <span className="font-mono-num text-blue-700">{result?.relation ?? '—'}</span>
            </span>
            <div className="flex items-center gap-3 text-[11px]">
              <span>Scheme (Blue)</span>
              <span aria-hidden="true">·</span>
              <span>Document (Amber)</span>
              <span aria-hidden="true">·</span>
              <span>State (Green)</span>
              <span aria-hidden="true">·</span>
              <span>Ministry (Slate)</span>
            </div>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-100 bg-slate-50/70">
            <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-[380px] min-w-[600px]">
              {/* Edges */}
              {result?.edges.map((edge, idx) => {
                const s = positioned.get(edge.source);
                const t = positioned.get(edge.target);
                if (!s || !t) return null;
                const mx = (s.x + t.x) / 2;
                const my = (s.y + t.y) / 2;
                const stroke =
                  edge.relation === 'mutually_exclusive_with'
                    ? '#DC2626'
                    : edge.relation === 'supersedes'
                      ? '#D97706'
                      : edge.relation === 'complementary_to'
                        ? '#15803D'
                        : '#94A3B8';
                return (
                  <g key={`edge-${idx}`}>
                    <line
                      x1={s.x}
                      y1={s.y}
                      x2={t.x}
                      y2={t.y}
                      stroke={stroke}
                      strokeWidth={edge.relation === 'complementary_to' || edge.relation === 'supersedes' ? 2 : 1.25}
                      strokeDasharray={edge.relation === 'mutually_exclusive_with' ? '5 4' : undefined}
                      opacity={0.75}
                    />
                    <text
                      x={mx}
                      y={my - 4}
                      textAnchor="middle"
                      fontSize="9"
                      fill="#475569"
                      fontFamily="JetBrains Mono, monospace"
                    >
                      {edge.relation}
                    </text>
                  </g>
                );
              })}

              {/* Nodes */}
              {Array.from(positioned.values()).map(({ x, y, node }) => {
                const style = NODE_COLORS[node.type] ?? NODE_COLORS.Ministry;
                const shortLabel = node.label.length > 26 ? `${node.label.slice(0, 24)}…` : node.label;
                return (
                  <g
                    key={node.id}
                    transform={`translate(${x}, ${y})`}
                    onClick={() => {
                      if (node.scheme_id) {
                        setAnchor(node.scheme_id);
                        void runQuery(`Schemes related to ${node.label}`, node.scheme_id);
                      }
                    }}
                    className={node.scheme_id ? 'cursor-pointer' : undefined}
                  >
                    <rect
                      x={-84}
                      y={-20}
                      width={168}
                      height={40}
                      rx={8}
                      fill={style.fill}
                      stroke={style.stroke}
                      strokeWidth={node.id === result?.nodes[0]?.id ? 2 : 1.2}
                    />
                    <text
                      x={0}
                      y={-4}
                      textAnchor="middle"
                      fontSize="8.5"
                      fill="#64748B"
                      fontFamily="JetBrains Mono, monospace"
                    >
                      {node.type}
                    </text>
                    <text
                      x={0}
                      y={10}
                      textAnchor="middle"
                      fontSize="10.5"
                      fontWeight={600}
                      fill={style.text}
                    >
                      {shortLabel}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Multi-Hop Reasoning Paths */}
        <div className="lg:col-span-4 rounded-xl border border-slate-200 bg-white p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Multi-Hop Evidence Paths</h3>
            <span className="font-mono-num text-xs text-slate-500">{result?.paths.length ?? 0} hops</span>
          </div>
          {!result || result.paths.length === 0 ? (
            <p className="text-xs text-slate-500">Click any Scheme node or run a preset to inspect multi-hop relations.</p>
          ) : (
            <ul className="space-y-2.5 text-xs">
              {result.paths.map((p, idx) => (
                <li key={idx} className="flex items-start gap-2 text-slate-700">
                  <GitBranch className="h-3.5 w-3.5 mt-0.5 shrink-0 text-blue-700" />
                  <span className="font-mono-num text-[11px] leading-relaxed">{p}</span>
                </li>
              ))}
            </ul>
          )}

          {result && result.matchedSchemes.length > 0 && (
            <div className="border-t border-slate-200 pt-3 space-y-2">
              <div className="text-xs font-semibold text-slate-800">Schemes Reached</div>
              <div className="space-y-1.5">
                {result.matchedSchemes.map((s) => (
                  <div key={s.scheme_id} className="flex items-center justify-between text-xs">
                    <span className="truncate text-slate-800">{s.name}</span>
                    <span className="font-mono-num text-slate-600 shrink-0">
                      ₹{s.annual_benefit_inr.toLocaleString('en-IN')}/yr
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
