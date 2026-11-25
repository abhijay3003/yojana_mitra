import React, { useEffect, useState } from 'react';
import {
  Check,
  CheckSquare,
  Copy,
  ExternalLink,
  Layers,
  MessageCircle,
  Square,
  Volume2,
} from 'lucide-react';
import type { CitizenProfile, StackOptimizationResult } from '../lib/types';
import {
  buildWhatsAppShareUrl,
  formatBenefitStackShareText,
  isTtsSupported,
  speakText,
  stopSpeaking,
} from '../lib/voiceAndShare';

interface Props {
  profile: CitizenProfile;
  stack: StackOptimizationResult | null;
  maxSchemes: number;
  onMaxSchemesChange: (n: number) => void;
}

export const BenefitStackView: React.FC<Props> = ({
  profile,
  stack,
  maxSchemes,
  onMaxSchemesChange,
}) => {
  const [checkedDocs, setCheckedDocs] = useState<Record<string, boolean>>({});
  const [speaking, setSpeaking] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    return () => stopSpeaking();
  }, []);

  const toggleDoc = (doc: string) => {
    setCheckedDocs((prev) => ({ ...prev, [doc]: !prev[doc] }));
  };

  // Deduplicated document checklist across the entire optimal stack (F10)
  const uniqueDocs: { doc: string; usedBy: string[] }[] = [];
  if (stack) {
    const docMap = new Map<string, string[]>();
    for (const s of stack.selected_schemes) {
      for (const d of s.documents) {
        const list = docMap.get(d) ?? [];
        list.push(s.name);
        docMap.set(d, list);
      }
    }
    docMap.forEach((usedBy, doc) => uniqueDocs.push({ doc, usedBy }));
  }

  const readyCount = uniqueDocs.filter((d) => checkedDocs[d.doc]).length;

  const shareText =
    stack && stack.selected_schemes.length > 0
      ? formatBenefitStackShareText(
          profile,
          stack,
          uniqueDocs.map((d) => d.doc)
        )
      : '';

  const handleToggleSpeak = () => {
    if (!shareText) return;
    if (speaking) {
      stopSpeaking();
      setSpeaking(false);
      return;
    }
    speakText(shareText, 'en', {
      onStart: () => setSpeaking(true),
      onEnd: () => setSpeaking(false),
    });
  };

  const handleCopyStack = async () => {
    if (!shareText) return;
    try {
      await navigator.clipboard.writeText(shareText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore clipboard restriction
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Benefit-Stacking Optimizer (F1 &amp; F10)</h2>
          <p className="text-xs text-slate-500">
            Exact combinatorial solver maximizing annual welfare (₹/year) across deterministically ELIGIBLE schemes while enforcing mutual-exclusion constraints.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {shareText && (
            <>
              {isTtsSupported() && (
                <button
                  type="button"
                  onClick={handleToggleSpeak}
                  className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors whitespace-nowrap ${
                    speaking
                      ? 'border-blue-300 bg-blue-50 text-blue-800'
                      : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <Volume2 className="h-3.5 w-3.5" />
                  {speaking ? 'Stop Audio' : 'Read Aloud'}
                </button>
              )}
              <button
                type="button"
                onClick={() => void handleCopyStack()}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors whitespace-nowrap"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? 'Copied' : 'Copy Stack'}
              </button>
              <a
                href={buildWhatsAppShareUrl(shareText)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-800 transition-colors whitespace-nowrap"
              >
                <MessageCircle className="h-3.5 w-3.5" />
                Share on WhatsApp
              </a>
            </>
          )}

          <div className="flex items-center gap-2">
            <label htmlFor="max-schemes" className="text-xs font-medium text-slate-700 whitespace-nowrap">
              Max Stacked
            </label>
            <select
              id="max-schemes"
              value={maxSchemes}
              onChange={(e) => onMaxSchemesChange(Number(e.target.value))}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-mono-num font-semibold text-slate-900"
            >
              {[3, 4, 5, 6].map((n) => (
                <option key={n} value={n}>
                  Top {n}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* KPI Strip */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="text-xs text-slate-500">Optimal Stacked Value</div>
          <div className="mt-1 font-mono-num text-2xl font-bold text-slate-900">
            ₹{(stack?.total_annual_inr ?? 0).toLocaleString('en-IN')}
          </div>
          <div className="mt-1 text-xs text-slate-500">per year ({stack?.selected_schemes.length ?? 0} schemes)</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="text-xs text-slate-500">Naive Top-1 Scheme</div>
          <div className="mt-1 font-mono-num text-2xl font-bold text-slate-700">
            ₹{(stack?.naive_top1_inr ?? 0).toLocaleString('en-IN')}
          </div>
          <div className="mt-1 text-xs text-slate-500">single highest scheme only</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="text-xs text-slate-500">Stacking Gain vs Top-1</div>
          <div className="mt-1 font-mono-num text-2xl font-bold text-emerald-700">
            +{stack?.gain_vs_top1_pct ?? 0}%
          </div>
          <div className="mt-1 font-mono-num text-xs text-emerald-700">
            +₹{(stack?.gain_vs_top1_inr ?? 0).toLocaleString('en-IN')}/yr extra unlocked
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="text-xs text-slate-500">Eligible Pool Screened</div>
          <div className="mt-1 font-mono-num text-2xl font-bold text-slate-900">
            {stack?.eligible_count ?? 0}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {profile.state} · {profile.category} · {profile.occupation}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
        {/* Selected Optimal Stack Table */}
        <div className="lg:col-span-7 rounded-xl border border-slate-200 bg-white p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Selected Non-Conflicting Scheme Stack</h3>
            <span className="font-mono-num text-xs text-slate-500">Solver: {stack?.solver ?? 'cp_sat'}</span>
          </div>

          {!stack || stack.selected_schemes.length === 0 ? (
            <p className="text-sm text-slate-500">
              No eligible schemes matched the current citizen profile. Adjust income, state, or occupation in the Eligibility Wizard.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500">
                    <th className="py-2 pr-4 font-medium">Scheme</th>
                    <th className="py-2 pr-4 font-medium">Jurisdiction</th>
                    <th className="py-2 pr-4 text-right font-medium">Annual Value</th>
                    <th className="py-2 text-right font-medium">Official Link</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {stack.selected_schemes.map((s) => (
                    <tr key={s.scheme_id} className="hover:bg-slate-50">
                      <td className="py-3 pr-4">
                        <div className="font-semibold text-slate-900">{s.name}</div>
                        <div className="text-[11px] text-slate-500">{s.category} · {s.scheme_id}</div>
                      </td>
                      <td className="py-3 pr-4 text-slate-700">{s.state}</td>
                      <td className="py-3 pr-4 text-right font-mono-num font-semibold text-slate-900">
                        ₹{s.annual_benefit_inr.toLocaleString('en-IN')}
                      </td>
                      <td className="py-3 text-right">
                        <a
                          href={s.apply_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 font-medium text-blue-700 hover:underline whitespace-nowrap"
                        >
                          Apply <ExternalLink className="h-3 w-3" />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Excluded due to mutual exclusion */}
          {stack && stack.excluded_by_conflict.length > 0 && (
            <div className="border-t border-slate-200 pt-4 space-y-2">
              <h4 className="text-xs font-semibold text-slate-800">
                Excluded by Mutual-Exclusion Constraints ({stack.excluded_by_conflict.length})
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-600">
                {stack.excluded_by_conflict.map((ex) => (
                  <li key={ex.scheme_id} className="flex items-start gap-2">
                    <Layers className="h-3.5 w-3.5 mt-0.5 shrink-0 text-amber-600" />
                    <span>
                      <strong className="text-slate-800">{ex.name}</strong> skipped because it is mutually exclusive with{' '}
                      <strong className="text-slate-800">{ex.conflicts_with}</strong>.
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* F10: Unified Document Checklist across Stacked Schemes */}
        <div className="lg:col-span-5 rounded-xl border border-slate-200 bg-white p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Unified Document Checklist (F10)</h3>
            <span className="font-mono-num text-xs text-slate-600">
              {readyCount} / {uniqueDocs.length} ready
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Deduplicated documents required to apply for every scheme in your optimized stack.
          </p>

          <ul className="divide-y divide-slate-100">
            {uniqueDocs.map((item) => {
              const checked = Boolean(checkedDocs[item.doc]);
              return (
                <li key={item.doc} className="py-2.5">
                  <button
                    type="button"
                    onClick={() => toggleDoc(item.doc)}
                    className="w-full flex items-start gap-2.5 text-left"
                  >
                    {checked ? (
                      <CheckSquare className="h-4 w-4 mt-0.5 shrink-0 text-emerald-600" />
                    ) : (
                      <Square className="h-4 w-4 mt-0.5 shrink-0 text-slate-400" />
                    )}
                    <div className="min-w-0">
                      <div className={`text-xs font-medium ${checked ? 'line-through text-slate-400' : 'text-slate-900'}`}>
                        {item.doc}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        Shared by {item.usedBy.length} scheme{item.usedBy.length > 1 ? 's' : ''}: {item.usedBy.slice(0, 2).join(', ')}
                        {item.usedBy.length > 2 ? ` +${item.usedBy.length - 2}` : ''}
                      </div>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
};
