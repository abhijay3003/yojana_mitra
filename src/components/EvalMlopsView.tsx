import React, { useState } from 'react';
import { CheckCircle2, Download, NotebookText, XCircle } from 'lucide-react';
import type { EvalReport } from '../lib/types';

interface Props {
  evalReport: EvalReport | null;
  feedbackSummary: { total: number; positive: number; negative: number };
}

const NOTEBOOKS = [
  { id: 'N1_embedder_ft.ipynb', base: 'intfloat/multilingual-e5-small', goal: '3,000+ multilingual query-scheme pairs · MNRL · target +10 pts Hit@5' },
  { id: 'N2_reranker_ft.ipynb', base: 'BAAI/bge-reranker-v2-m3', goal: 'Hard negatives mined from SQLite thumbs-down feedback logs' },
  { id: 'N3_extractor_ft.ipynb', base: 'bert-base-multilingual-cased', goal: '500 labeled schemes -> 10-field /rules/schema.json · F1 >= 0.85' },
  { id: 'N4_intent_clf.ipynb', base: 'distilbert-base-multilingual-cased', goal: '1,500 5-language queries across 5 intents · Macro F1 >= 0.90' },
  { id: 'N5_scam_clf.ipynb', base: 'distilbert-base-multilingual-cased', goal: '2,000 scam vs official .gov.in notices · F1 >= 0.92' },
  { id: 'N6_qlora_dpo.ipynb', base: 'Qwen/Qwen2.5-7B-Instruct', goal: '5,000+ trilingual SFT + DPO grounded explanations · win rate >= 65%' },
];

export const EvalMlopsView: React.FC<Props> = ({ evalReport, feedbackSummary }) => {
  const [hardNegExport, setHardNegExport] = useState<string | null>(null);

  const exportHardNegatives = async () => {
    const res = await fetch('/api/feedback/export');
    if (res.ok) {
      const data = await res.json();
      setHardNegExport(JSON.stringify(data, null, 2));
    }
  };

  if (!evalReport) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
        Evaluation report not yet generated. Run <code className="font-mono-num">python3 -m eval.run_all_evals</code> to compute metrics.
      </div>
    );
  }

  const passCount = evalReport.targets.filter((t) => t.status === 'PASS').length;
  const missedCount = evalReport.targets.length - passCount;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Evaluation, Fairness &amp; MLOps Audit (P7 &amp; P11)</h2>
          <p className="text-xs text-slate-500">
            Exact measured metrics computed from <code className="font-mono-num">data/gold/*.jsonl</code> (seed={evalReport.seed}). Unexecuted GPU/human metrics are honestly marked MISSED with cause and fix.
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className="font-mono-num font-semibold text-emerald-700">{passCount} PASS</span>
          <span aria-hidden="true" className="text-slate-300">·</span>
          <span className="font-mono-num font-semibold text-amber-700">{missedCount} MISSED / PENDING</span>
        </div>
      </div>

      {/* Retrieval Ablation + GraphRAG Comparison */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 items-start">
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
          <h3 className="text-sm font-semibold text-slate-900">Retrieval Layer Ablation (100 5-Language Gold Queries)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="py-2 pr-4 font-medium">Layer</th>
                  <th className="py-2 pr-4 text-right font-medium">Hit@5</th>
                  <th className="py-2 pr-4 text-right font-medium">MRR</th>
                  <th className="py-2 text-right font-medium">Avg Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {evalReport.retrieval.ablations.map((row) => (
                  <tr key={row.layer} className="hover:bg-slate-50">
                    <td className="py-2 pr-4 font-mono-num font-medium text-slate-900">{row.layer}</td>
                    <td className="py-2 pr-4 text-right font-mono-num font-semibold text-slate-900">{row.hit_at_5}%</td>
                    <td className="py-2 pr-4 text-right font-mono-num text-slate-700">{row.mrr}</td>
                    <td className="py-2 text-right font-mono-num text-slate-600">{row.avg_latency_ms} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-slate-200 pt-3 flex items-center justify-between text-xs">
            <span className="text-slate-600">GraphRAG vs Vanilla BM25 (40 Multi-Hop Qs)</span>
            <span className="font-mono-num font-semibold text-emerald-700">
              {evalReport.multihop.graphrag_acc}% vs {evalReport.multihop.vanilla_rag_acc}% (+{evalReport.multihop.gain_pts} pts)
            </span>
          </div>
        </div>

        {/* P11 Fairness Slice Table */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Fairness Slice Audit (Flag Gap &gt; 5 pts)</h3>
            <span className="font-mono-num text-xs text-slate-500">Drift PSI: {evalReport.drift.psi} ({evalReport.drift.severity})</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between font-medium text-slate-700 mb-1">
                <span>By Language (Hit@5)</span>
                <span className={`font-mono-num font-semibold ${evalReport.fairness.language_flag ? 'text-red-700' : 'text-emerald-700'}`}>
                  Gap: {evalReport.fairness.language_gap_pts} pts {evalReport.fairness.language_flag ? '(FLAGGED)' : '(OK)'}
                </span>
              </div>
              <div className="grid grid-cols-5 gap-2">
                {Object.entries(evalReport.fairness.language_hit5).map(([l, v]) => (
                  <div key={l} className="rounded-md bg-slate-50 p-2 text-center">
                    <div className="text-[11px] text-slate-500">{l.toUpperCase()}</div>
                    <div className="font-mono-num font-semibold text-slate-900">{v}%</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="flex justify-between font-medium text-slate-700 mb-1">
                <span>By Social Category (Verdict Accuracy)</span>
                <span className={`font-mono-num font-semibold ${evalReport.fairness.category_flag ? 'text-red-700' : 'text-emerald-700'}`}>
                  Gap: {evalReport.fairness.category_gap_pts} pts {evalReport.fairness.category_flag ? '(FLAGGED)' : '(OK)'}
                </span>
              </div>
              <div className="grid grid-cols-5 gap-2">
                {Object.entries(evalReport.fairness.category_verdict_acc).map(([c, v]) => (
                  <div key={c} className="rounded-md bg-slate-50 p-2 text-center">
                    <div className="text-[11px] text-slate-500">{c}</div>
                    <div className="font-mono-num font-semibold text-slate-900">{v}%</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-slate-100 pt-2">
              <span className="text-slate-600">
                Gender Verdict Accuracy: Female <strong className="font-mono-num">{evalReport.fairness.gender_verdict_acc.Female}%</strong> · Male{' '}
                <strong className="font-mono-num">{evalReport.fairness.gender_verdict_acc.Male}%</strong>
              </span>
              <span className="font-mono-num font-semibold text-emerald-700">Gap: {evalReport.fairness.gender_gap_pts} pts</span>
            </div>
          </div>
        </div>
      </div>

      {/* Full Honest PASS / MISSED Target Table */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
        <h3 className="text-sm font-semibold text-slate-900">Final Targets Scorecard (Exact Measured Numbers)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2 pr-4 font-medium">Metric</th>
                <th className="py-2 pr-4 font-medium">Target</th>
                <th className="py-2 pr-4 font-medium">Measured</th>
                <th className="py-2 pr-4 font-medium">Status</th>
                <th className="py-2 font-medium">Cause / Verification Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {evalReport.targets.map((t) => (
                <tr key={t.metric} className="hover:bg-slate-50">
                  <td className="py-2.5 pr-4 font-medium text-slate-900">{t.metric}</td>
                  <td className="py-2.5 pr-4 font-mono-num text-slate-600 whitespace-nowrap">{t.target}</td>
                  <td className="py-2.5 pr-4 font-mono-num font-semibold text-slate-900 whitespace-nowrap">{t.measured}</td>
                  <td className="py-2.5 pr-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center gap-1 font-semibold ${
                        t.status === 'PASS' ? 'text-emerald-700' : 'text-amber-700'
                      }`}
                    >
                      {t.status === 'PASS' ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}
                      {t.status}
                    </span>
                  </td>
                  <td className="py-2.5 text-slate-600">{t.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* P7 Kaggle T4 Notebooks & F8 Feedback Hard-Negative Export */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
        <div className="lg:col-span-8 rounded-xl border border-slate-200 bg-white p-5 space-y-3">
          <h3 className="text-sm font-semibold text-slate-900">Kaggle / Colab T4 Training Notebooks (P7 · Seed 42)</h3>
          <div className="divide-y divide-slate-100">
            {NOTEBOOKS.map((nb) => (
              <div key={nb.id} className="py-2.5 flex items-start justify-between gap-4 text-xs">
                <div className="flex items-start gap-2">
                  <NotebookText className="h-4 w-4 mt-0.5 shrink-0 text-blue-700" />
                  <div>
                    <div className="font-mono-num font-semibold text-slate-900">notebooks/{nb.id}</div>
                    <div className="text-slate-600">{nb.goal}</div>
                  </div>
                </div>
                <span className="font-mono-num text-[11px] text-slate-500 shrink-0">{nb.base}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-4 rounded-xl border border-slate-200 bg-white p-5 space-y-3">
          <h3 className="text-sm font-semibold text-slate-900">Feedback &amp; Hard-Negative Loop (F8)</h3>
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="rounded-md bg-slate-50 p-2">
              <div className="text-slate-500">Logged</div>
              <div className="font-mono-num text-base font-bold text-slate-900">{feedbackSummary.total}</div>
            </div>
            <div className="rounded-md bg-slate-50 p-2">
              <div className="text-slate-500">Positive</div>
              <div className="font-mono-num text-base font-bold text-emerald-700">{feedbackSummary.positive}</div>
            </div>
            <div className="rounded-md bg-slate-50 p-2">
              <div className="text-slate-500">Hard Neg.</div>
              <div className="font-mono-num text-base font-bold text-amber-700">{feedbackSummary.negative}</div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => void exportHardNegatives()}
            className="w-full inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <Download className="h-3.5 w-3.5" /> Inspect Hard-Negative Export
          </button>
          {hardNegExport && (
            <pre className="max-h-40 overflow-auto rounded-lg bg-slate-900 p-2.5 font-mono-num text-[10px] text-slate-100">
              {hardNegExport}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};
