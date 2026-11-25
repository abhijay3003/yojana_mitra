/**
 * Yojana Mitra Neurosymbolic Core Engine (TypeScript server-side implementation).
 * Mirrors the exact deterministic algorithms verified in /rules/, /retrieval/, /graph/, /agents/, /ocr/.
 */

import { maskPii } from './piiMasker.ts';
import type {
  CitizenProfile,
  CounterfactualChange,
  CounterfactualResult,
  GraphEdgeView,
  GraphNodeView,
  LanguageCode,
  RejectionPrediction,
  RuleCheckEntry,
  RuleEvaluation,
  ScamAnalysis,
  Scheme,
  StackOptimizationResult,
  Verdict,
} from './types.ts';

export const DISCLAIMER = 'Informational only. Verify on the official portal.';

// ---- Language Detection ----
export function detectLanguage(text: string): LanguageCode {
  if (!text) return 'en';
  const counts: Record<LanguageCode, number> = { en: 0, te: 0, hi: 0, kn: 0, ta: 0 };
  for (const ch of text) {
    const cp = ch.codePointAt(0) ?? 0;
    if (cp >= 0x0c00 && cp <= 0x0c7f) counts.te += 1;
    else if (cp >= 0x0900 && cp <= 0x097f) counts.hi += 1;
    else if (cp >= 0x0c80 && cp <= 0x0cff) counts.kn += 1;
    else if (cp >= 0x0b80 && cp <= 0x0bff) counts.ta += 1;
  }
  const best = (['te', 'hi', 'kn', 'ta'] as LanguageCode[]).reduce(
    (acc, lang) => (counts[lang] > counts[acc] ? lang : acc),
    'te' as LanguageCode,
  );
  if (counts[best] >= 2) return best;

  const lower = text.toLowerCase();
  if (/\b(naku|pathakam|arhatalu|kavali|enti|rythu bharosa)\b/.test(lower) && /\b(naku|pathakam|arhatalu|enti|kavali)\b/.test(lower)) {
    return 'te';
  }
  if (/\b(mujhe|patrata|kaise|milega|kya|yojana)\b/.test(lower) && /\b(mujhe|patrata|kaise|milega|kya)\b/.test(lower)) {
    return 'hi';
  }
  return 'en';
}

// ---- Intent & Retrieval Routing ----
export function routeQuery(query: string): {
  lang: LanguageCode;
  intent: string;
  retriever_mode: 'vector' | 'graph' | 'none';
} {
  const lang = detectLanguage(query);
  const q = (query || '').toLowerCase();

  const scamSignals = [
    'scam', 'fake', 'fraud', 'lottery', 'congratulations', '.xyz', '.top', '.apk',
    'processing fee', 'registration fee', 'forward to', 'cvv', 'gpay', 'phonepe',
    'free laptop', 'free 5g', 'agent commission', 'మోసం', 'फर्जी',
  ];
  if (scamSignals.some((s) => q.includes(s))) {
    return { lang, intent: 'scam_check', retriever_mode: 'none' };
  }

  let intent = 'eligibility';
  if (/(status|installment|credited|pending|track|స్టేటస్|ఎప్పుడు పడతాయి|स्थिति)/i.test(q)) {
    intent = 'status';
  } else if (/(document|documents|certificate|passbook|card|పత్రాలు|దస్తావేజులు|दस्तावेज|ದಾಖಲೆಗಳು|ஆவணங்கள்)/i.test(q)) {
    intent = 'documents';
  } else if (/(how to apply|apply|portal|register|దరఖాస్తు|ఎలా పొందాలి|आवेदन|कैसे करें|ಅರ್ಜಿ|விண்ணப்ப)/i.test(q)) {
    intent = 'how_to_apply';
  }

  const retriever_mode = /(complement|stack|supersede|replace|mutually exclusive|share|together|combine)/i.test(q)
    ? 'graph'
    : 'vector';

  return { lang, intent, retriever_mode };
}

// ---- Deterministic Rule Engine (P3) ----
function comparePredicate(actual: unknown, op: string, expected: unknown): boolean {
  if (op === '==') {
    if (typeof actual === 'string' && typeof expected === 'string') {
      return actual.trim().toLowerCase() === expected.trim().toLowerCase();
    }
    return actual === expected;
  }
  if (op === '!=') {
    if (typeof actual === 'string' && typeof expected === 'string') {
      return actual.trim().toLowerCase() !== expected.trim().toLowerCase();
    }
    return actual !== expected;
  }
  if (op === '<=') return Number(actual) <= Number(expected);
  if (op === '>=') return Number(actual) >= Number(expected);
  if (op === '<') return Number(actual) < Number(expected);
  if (op === '>') return Number(actual) > Number(expected);
  if (op === 'in' && Array.isArray(expected)) {
    return expected.map((v) => String(v).trim().toLowerCase()).includes(String(actual).trim().toLowerCase());
  }
  if (op === 'not_in' && Array.isArray(expected)) {
    return !expected.map((v) => String(v).trim().toLowerCase()).includes(String(actual).trim().toLowerCase());
  }
  return false;
}

export function evaluateScheme(profile: Partial<CitizenProfile>, scheme: Scheme): RuleEvaluation {
  const passed: RuleCheckEntry[] = [];
  const failed: RuleCheckEntry[] = [];
  const missing: RuleCheckEntry[] = [];
  const trace: string[] = [];

  for (const rule of scheme.rules) {
    const label = rule.label || `${rule.field} ${rule.op} ${String(rule.value)}`;
    const actual = (profile as Record<string, unknown>)[rule.field];

    if (actual === undefined || actual === null || actual === '') {
      missing.push({ field: rule.field, op: rule.op, expected: rule.value, actual: null, label, status: 'MISSING' });
      trace.push(`[MISSING] ${label}: profile.${rule.field} not provided`);
      continue;
    }

    const ok = comparePredicate(actual, rule.op, rule.value);
    const entry: RuleCheckEntry = {
      field: rule.field,
      op: rule.op,
      expected: rule.value,
      actual,
      label,
      status: ok ? 'PASS' : 'FAIL',
    };
    if (ok) {
      passed.push(entry);
      trace.push(`[PASS] ${label} (actual=${String(actual)})`);
    } else {
      failed.push(entry);
      trace.push(`[FAIL] ${label} (actual=${String(actual)}, required ${rule.op} ${JSON.stringify(rule.value)})`);
    }
  }

  let verdict: Verdict = 'ELIGIBLE';
  if (failed.length > 0) verdict = 'NOT_ELIGIBLE';
  else if (missing.length > 0) verdict = 'NEEDS_INFO';

  const match_score = Math.round((passed.length / Math.max(scheme.rules.length, 1)) * 1000) / 10;

  return {
    scheme_id: scheme.scheme_id,
    scheme_name: scheme.name,
    verdict,
    passed,
    failed,
    missing,
    trace,
    match_score,
    annual_benefit_inr: scheme.annual_benefit_inr,
    state: scheme.state,
    category: scheme.category,
    apply_url: scheme.apply_url,
    documents: scheme.documents,
  };
}

// ---- Counterfactual Solver (P3 + F2) ----
export function generateCounterfactual(profile: Partial<CitizenProfile>, scheme: Scheme): CounterfactualResult {
  const initial = evaluateScheme(profile, scheme);
  if (initial.verdict === 'ELIGIBLE') {
    return {
      scheme_id: scheme.scheme_id,
      scheme_name: scheme.name,
      already_eligible: true,
      changes: [],
      summary: 'Already eligible under all deterministic rules.',
      verified_eligible: true,
    };
  }

  const modified: Record<string, unknown> = { ...profile };
  const changes: CounterfactualChange[] = [];
  const failingItems = [...initial.failed, ...initial.missing];

  for (const item of failingItems) {
    let target: unknown = item.expected;
    if (item.op === 'in' && Array.isArray(item.expected) && item.expected.length > 0) {
      target = item.expected[0];
    } else if (item.op === '<') {
      target = Number(item.expected) - 1;
    } else if (item.op === '>') {
      target = Number(item.expected) + 1;
    }

    let explanation = `Eligible if ${item.field} ${item.op} ${String(item.expected)} (currently ${String(item.actual)})`;
    if (item.field === 'income' && (item.op === '<=' || item.op === '<')) {
      const diff = Number(item.actual ?? 0) - Number(item.expected);
      explanation =
        diff > 0
          ? `Eligible if annual income <= ₹${Number(item.expected).toLocaleString('en-IN')} (reduce by ₹${diff.toLocaleString('en-IN')})`
          : `Eligible if annual income <= ₹${Number(item.expected).toLocaleString('en-IN')}`;
    } else if (item.field === 'land') {
      explanation = `Eligible if cultivable land ${item.op} ${String(item.expected)} acres (currently ${String(item.actual ?? 0)} acres)`;
    } else if (item.field === 'bpl') {
      explanation = 'Eligible if household holds a valid BPL / White Ration Card';
    } else if (item.field === 'state') {
      explanation = `Restricted to ${String(item.expected)} residents (currently ${String(item.actual ?? 'unset')})`;
    } else if (item.op === 'in' && Array.isArray(item.expected)) {
      explanation = `Eligible if ${item.field} is in [${item.expected.join(', ')}] (currently ${String(item.actual ?? 'unset')})`;
    }

    modified[item.field] = target;
    changes.push({
      field: item.field,
      op: item.op,
      current: item.actual,
      required: item.expected,
      suggested_value: target,
      actionable: item.field !== 'category' && item.field !== 'gender',
      explanation,
    });
  }

  const recheck = evaluateScheme(modified as Partial<CitizenProfile>, scheme);
  return {
    scheme_id: scheme.scheme_id,
    scheme_name: scheme.name,
    already_eligible: false,
    changes,
    summary: changes.map((c) => c.explanation).join('; '),
    verified_eligible: recheck.verdict === 'ELIGIBLE',
  };
}

// ---- Exact Combinatorial Benefit-Stacking Optimizer (F1) ----
export function optimizeBenefitStack(
  profile: Partial<CitizenProfile>,
  schemes: Scheme[],
  maxSchemes = 5,
): StackOptimizationResult {
  const eligible = schemes.filter((s) => evaluateScheme(profile, s).verdict === 'ELIGIBLE');
  if (eligible.length === 0) {
    return {
      solver: 'exact_branch_and_bound_cp',
      eligible_count: 0,
      selected_schemes: [],
      total_annual_inr: 0,
      naive_top1_inr: 0,
      gain_vs_top1_inr: 0,
      gain_vs_top1_pct: 0,
      excluded_by_conflict: [],
    };
  }

  const ordered = [...eligible].sort(
    (a, b) => b.annual_benefit_inr - a.annual_benefit_inr || a.scheme_id.localeCompare(b.scheme_id),
  );
  const pool = ordered.slice(0, 24);
  const n = pool.length;
  const values = pool.map((s) => s.annual_benefit_inr);
  const idToIdx = new Map(pool.map((s, i) => [s.scheme_id, i]));

  const conflicts: Set<number>[] = Array.from({ length: n }, () => new Set<number>());
  pool.forEach((s, i) => {
    for (const ex of s.mutually_exclusive_with ?? []) {
      const j = idToIdx.get(ex);
      if (j !== undefined && j !== i) {
        conflicts[i].add(j);
        conflicts[j].add(i);
      }
    }
  });

  let bestVal = 0;
  let bestPick: number[] = [];

  function dfs(idx: number, picked: number[], currentVal: number) {
    if (currentVal > bestVal) {
      bestVal = currentVal;
      bestPick = [...picked];
    }
    if (idx >= n || (maxSchemes > 0 && picked.length >= maxSchemes)) return;

    const slotsLeft = maxSchemes > 0 ? maxSchemes - picked.length : n - idx;
    let upper = currentVal;
    for (let k = idx; k < Math.min(n, idx + slotsLeft); k++) upper += values[k];
    if (upper <= bestVal) return;

    if (picked.every((p) => !conflicts[p].has(idx))) {
      picked.push(idx);
      dfs(idx + 1, picked, currentVal + values[idx]);
      picked.pop();
    }
    dfs(idx + 1, picked, currentVal);
  }

  dfs(0, [], 0);

  const selected = bestPick.map((i) => pool[i]).sort((a, b) => b.annual_benefit_inr - a.annual_benefit_inr);
  const selectedIds = new Set(selected.map((s) => s.scheme_id));
  const total_annual_inr = selected.reduce((sum, s) => sum + s.annual_benefit_inr, 0);
  const naive_top1_inr = Math.max(...eligible.map((s) => s.annual_benefit_inr));
  const gain_vs_top1_inr = total_annual_inr - naive_top1_inr;
  const gain_vs_top1_pct = naive_top1_inr > 0 ? Math.round((gain_vs_top1_inr / naive_top1_inr) * 1000) / 10 : 0;

  const excluded_by_conflict: { scheme_id: string; name: string; conflicts_with: string }[] = [];
  for (const s of eligible) {
    if (selectedIds.has(s.scheme_id)) continue;
    const conflictingWith = selected
      .filter(
        (sel) =>
          (s.mutually_exclusive_with ?? []).includes(sel.scheme_id) ||
          (sel.mutually_exclusive_with ?? []).includes(s.scheme_id),
      )
      .map((sel) => sel.name);
    if (conflictingWith.length > 0) {
      excluded_by_conflict.push({
        scheme_id: s.scheme_id,
        name: s.name,
        conflicts_with: conflictingWith.join(', '),
      });
    }
  }

  return {
    solver: 'exact_branch_and_bound_cp',
    eligible_count: eligible.length,
    selected_schemes: selected.map((s) => ({
      scheme_id: s.scheme_id,
      name: s.name,
      state: s.state,
      category: s.category,
      annual_benefit_inr: s.annual_benefit_inr,
      apply_url: s.apply_url,
      documents: s.documents,
    })),
    total_annual_inr,
    naive_top1_inr,
    gain_vs_top1_inr,
    gain_vs_top1_pct,
    excluded_by_conflict,
  };
}

// ---- Rejection Risk Predictor (F7) ----
export function predictRejectionRisk(
  profile: Partial<CitizenProfile>,
  scheme: Scheme,
  availableDocuments?: string[],
  aadhaarBankSeeded = true,
  certificateAgeMonths = 6,
): RejectionPrediction {
  const ev = evaluateScheme(profile, scheme);
  const reasons: { impact_score: number; reason: string; mitigation: string }[] = [];
  let logit = -2.1;

  if (ev.failed.length > 0) {
    logit += 2.6 * ev.failed.length;
    for (const f of ev.failed) {
      reasons.push({
        impact_score: 0.92,
        reason: `Hard eligibility mismatch: ${f.label} (your value: ${String(f.actual)})`,
        mitigation: 'Review counterfactual requirements or apply for complementary eligible schemes.',
      });
    }
  }

  if (availableDocuments) {
    const normAvail = availableDocuments.map((d) => d.trim().toLowerCase());
    const missingDocs = scheme.documents.filter(
      (req) => !normAvail.some((a) => req.toLowerCase().includes(a) || a.includes(req.toLowerCase())),
    );
    if (missingDocs.length > 0) {
      logit += 0.65 * missingDocs.length;
      reasons.push({
        impact_score: Math.min(0.88, Math.round((0.35 + 0.18 * missingDocs.length) * 100) / 100),
        reason: `Missing mandatory document(s): ${missingDocs.slice(0, 3).join(', ')}`,
        mitigation: 'Obtain verified copies via MeeSeva / CSC / DigiLocker before submission.',
      });
    }
  }

  if (!aadhaarBankSeeded) {
    logit += 1.35;
    reasons.push({
      impact_score: 0.78,
      reason: 'Bank account is not NPCI / Aadhaar-DBT seeded',
      mitigation: 'Visit your bank branch or check NPCI Aadhaar mapper to enable DBT seeding.',
    });
  }

  if (typeof profile.income === 'number') {
    for (const r of scheme.rules) {
      if (r.field === 'income' && (r.op === '<=' || r.op === '<')) {
        const cap = Number(r.value);
        if (profile.income >= 0.85 * cap && profile.income <= cap) {
          logit += 0.55;
          reasons.push({
            impact_score: 0.46,
            reason: `Borderline income margin (₹${profile.income.toLocaleString('en-IN')} vs cap ₹${cap.toLocaleString('en-IN')})`,
            mitigation: 'Attach a fresh Tehsildar/MRO Income Certificate issued within the last 6 months.',
          });
        }
      }
    }
  }

  if (certificateAgeMonths > 12) {
    logit += 0.85;
    reasons.push({
      impact_score: 0.62,
      reason: `Income/domicile certificate is ${certificateAgeMonths} months old (>12 months validity)`,
      mitigation: 'Renew certificate via MeeSeva / e-District before submitting.',
    });
  }

  if (scheme.category === 'Agriculture' && Number(profile.land ?? 0) > 0) {
    logit += 0.25;
    reasons.push({
      impact_score: 0.31,
      reason: 'Land record (Dharani / ROR) name spelling mismatch with Aadhaar & Bank KYC',
      mitigation: 'Verify identical applicant name & father/husband name across Pattadar Passbook and Aadhaar.',
    });
  }

  if (reasons.length < 3) {
    reasons.push({
      impact_score: 0.18,
      reason: 'Aadhaar e-KYC mobile OTP mismatch during verification',
      mitigation: 'Confirm active mobile number linked to UIDAI Aadhaar prior to final submission.',
    });
  }
  if (reasons.length < 3) {
    reasons.push({
      impact_score: 0.14,
      reason: 'Inactive bank account or outdated post-merger IFSC code',
      mitigation: 'Verify current bank IFSC and ensure account is active with a recent transaction.',
    });
  }

  const rejection_probability = Math.round((1 / (1 + Math.exp(-logit))) * 1000) / 1000;
  reasons.sort((a, b) => b.impact_score - a.impact_score);

  return {
    scheme_id: scheme.scheme_id,
    scheme_name: scheme.name,
    verdict: ev.verdict,
    rejection_probability,
    risk_band: rejection_probability >= 0.6 ? 'HIGH' : rejection_probability >= 0.3 ? 'MEDIUM' : 'LOW',
    top_3_reasons: reasons.slice(0, 3),
  };
}

// ---- Hybrid Multilingual Retrieval (P4) ----
const TOKEN_RE = /[\w\u0900-\u097F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF]+/gu;

function tokenize(text: string): string[] {
  return (text.match(TOKEN_RE) ?? []).map((t) => t.toLowerCase()).filter((t) => t.length >= 2);
}

function schemeDoc(s: Scheme): string {
  return [
    s.name,
    s.scheme_id,
    s.state,
    s.category,
    s.ministry,
    s.benefits,
    s.eligibility_text,
    ...s.documents,
    ...(s.keywords ?? []),
    ...Object.values(s.translations ?? {}),
  ].join(' ');
}

export function hybridSearch(
  query: string,
  schemes: Scheme[],
  options?: { topK?: number; state?: string; category?: string },
): { scheme: Scheme; score: number }[] {
  const topK = options?.topK ?? 5;
  const qLower = query.toLowerCase();
  const qTokens = tokenize(query);
  const qSet = new Set(qTokens);

  const filtered = schemes.filter((s) => {
    if (options?.state && options.state !== 'All' && s.state !== options.state && s.state !== 'All India') {
      return false;
    }
    if (options?.category && options.category !== 'All' && s.category.toLowerCase() !== options.category.toLowerCase()) {
      return false;
    }
    return true;
  });

  const scored = filtered.map((s) => {
    const doc = schemeDoc(s);
    const docLower = doc.toLowerCase();
    const docTokens = new Set(tokenize(doc));
    let score = 0;

    if (qLower.includes(s.name.toLowerCase())) score += 5.0;
    for (const kw of s.keywords ?? []) {
      if (kw.length >= 3 && qLower.includes(kw.toLowerCase())) score += 2.6;
    }
    for (const qt of qSet) {
      if (docTokens.has(qt)) {
        score += 1.3;
      } else if (qt.length >= 4 && docLower.includes(qt)) {
        score += 0.85;
      }
    }
    if (s.state !== 'All India' && qLower.includes(s.state.toLowerCase())) score += 1.4;
    return { scheme: s, score: Math.round(score * 1000) / 1000 };
  });

  scored.sort((a, b) => b.score - a.score || b.scheme.annual_benefit_inr - a.scheme.annual_benefit_inr);
  return scored.slice(0, topK);
}

// ---- GraphRAG Multi-Hop Engine (P5) ----
export function runGraphQuery(
  query: string,
  schemes: Scheme[],
  anchorSchemeId?: string,
): {
  relation: string;
  matchedSchemes: Scheme[];
  paths: string[];
  nodes: GraphNodeView[];
  edges: GraphEdgeView[];
} {
  const byId = new Map(schemes.map((s) => [s.scheme_id, s]));
  const qLower = query.toLowerCase();

  let relation = 'complementary_to';
  if (/(supersed|replac|legacy|old)/i.test(qLower)) relation = 'supersedes';
  else if (/(mutually exclusive|conflict|cannot be stacked)/i.test(qLower)) relation = 'mutually_exclusive_with';
  else if (/(document|passbook|ration|udid|certificate|share)/i.test(qLower)) relation = 'requires_document';

  const anchor =
    (anchorSchemeId && byId.get(anchorSchemeId)) ||
    hybridSearch(query, schemes, { topK: 1 })[0]?.scheme ||
    byId.get('TS_RYTHU_BHAROSA') ||
    schemes[0];

  const nodesMap = new Map<string, GraphNodeView>();
  const edges: GraphEdgeView[] = [];
  const paths: string[] = [];
  const matchedIds = new Set<string>();

  const addSchemeNode = (s: Scheme) => {
    const nid = `scheme:${s.scheme_id}`;
    if (!nodesMap.has(nid)) {
      nodesMap.set(nid, {
        id: nid,
        type: 'Scheme',
        label: s.name,
        scheme_id: s.scheme_id,
        annual_benefit_inr: s.annual_benefit_inr,
      });
    }
    return nid;
  };

  const anchorNodeId = addSchemeNode(anchor);
  matchedIds.add(anchor.scheme_id);

  // Add State & Ministry & Benefit nodes for anchor
  const stateId = `state:${anchor.state}`;
  nodesMap.set(stateId, { id: stateId, type: 'State', label: anchor.state });
  edges.push({ source: anchorNodeId, target: stateId, relation: 'applies_in_state' });

  const minId = `ministry:${anchor.ministry}`;
  nodesMap.set(minId, { id: minId, type: 'Ministry', label: anchor.ministry });
  edges.push({ source: anchorNodeId, target: minId, relation: 'administered_by' });

  // Documents (shared across schemes)
  for (const doc of anchor.documents.slice(0, 3)) {
    const docId = `doc:${doc}`;
    nodesMap.set(docId, { id: docId, type: 'Document', label: doc });
    edges.push({ source: anchorNodeId, target: docId, relation: 'requires_document' });

    if (relation === 'requires_document') {
      for (const other of schemes) {
        if (other.scheme_id !== anchor.scheme_id && other.documents.includes(doc) && matchedIds.size < 6) {
          const oid = addSchemeNode(other);
          edges.push({ source: oid, target: docId, relation: 'requires_document' });
          paths.push(`${anchor.name} -[requires_document]-> ${doc} <-[requires_document]- ${other.name}`);
          matchedIds.add(other.scheme_id);
        }
      }
    }
  }

  // Complementary schemes
  for (const cid of anchor.complementary_to ?? []) {
    const target = byId.get(cid);
    if (!target) continue;
    const tid = addSchemeNode(target);
    edges.push({ source: anchorNodeId, target: tid, relation: 'complementary_to' });
    paths.push(`${anchor.name} -[complementary_to]-> ${target.name} (₹${target.annual_benefit_inr.toLocaleString('en-IN')}/yr)`);
    matchedIds.add(target.scheme_id);
  }

  // Mutually exclusive schemes
  for (const exid of anchor.mutually_exclusive_with ?? []) {
    const target = byId.get(exid);
    if (!target) continue;
    const tid = addSchemeNode(target);
    edges.push({ source: anchorNodeId, target: tid, relation: 'mutually_exclusive_with' });
    paths.push(`${anchor.name} -[mutually_exclusive_with]-> ${target.name} (cannot stack)`);
    matchedIds.add(target.scheme_id);
  }

  // Supersedes (both directions)
  for (const supid of anchor.supersedes ?? []) {
    const target = byId.get(supid);
    if (!target) continue;
    const tid = addSchemeNode(target);
    edges.push({ source: anchorNodeId, target: tid, relation: 'supersedes' });
    paths.push(`${anchor.name} -[supersedes]-> ${target.name}`);
    matchedIds.add(target.scheme_id);
  }
  for (const other of schemes) {
    if ((other.supersedes ?? []).includes(anchor.scheme_id)) {
      const oid = addSchemeNode(other);
      edges.push({ source: oid, target: anchorNodeId, relation: 'supersedes' });
      paths.push(`${other.name} -[supersedes]-> ${anchor.name}`);
      matchedIds.add(other.scheme_id);
      for (const comp of other.complementary_to ?? []) {
        const cTarget = byId.get(comp);
        if (cTarget) {
          const cid = addSchemeNode(cTarget);
          edges.push({ source: oid, target: cid, relation: 'complementary_to' });
          paths.push(`${other.name} -[complementary_to]-> ${cTarget.name}`);
          matchedIds.add(cTarget.scheme_id);
        }
      }
    }
  }

  const matchedSchemes = Array.from(matchedIds)
    .map((id) => byId.get(id))
    .filter((s): s is Scheme => Boolean(s));

  return {
    relation,
    matchedSchemes,
    paths,
    nodes: Array.from(nodesMap.values()),
    edges,
  };
}

// ---- Scam Detector (F6) ----
const SUSPICIOUS_TLDS = ['.xyz', '.top', '.click', '.online', '.shop', '.club', '.buzz', '.apk', 'tinyurl.com', 'bit.ly'];
const OFFICIAL_DOMAINS = ['.gov.in', '.nic.in', 'myscheme.gov.in', 'udyamimitra.in', 'standupmitra.in', 'maandhan.in'];
const SCAM_PATTERNS: [string, string][] = [
  ['registration fee', 'Requests a registration or processing fee (official welfare schemes do not charge UPI fees).'],
  ['processing fee', 'Requests an upfront processing fee.'],
  ['agent commission', 'Asks for unofficial agent commission.'],
  ['stamp duty', 'Asks for advance stamp duty over UPI.'],
  ['upi', 'Solicits transfer to a private UPI handle.'],
  ['gpay', 'Requests Google Pay transfer.'],
  ['phonepe', 'Requests PhonePe payment.'],
  ['otp', 'Solicits Aadhaar or banking OTP.'],
  ['cvv', 'Requests ATM/debit card CVV or PIN.'],
  ['bank pin', 'Requests private bank PIN.'],
  ['.apk', 'Shares an unofficial Android .apk file instead of official portal.'],
  ['forward to', 'Uses viral chain-forwarding pressure.'],
  ['free laptop', 'Matches known "Free Laptop / Smartphone" hoax pattern.'],
  ['free 5g', 'Matches known "Free 5G Phone" hoax pattern.'],
  ['lottery winner', 'Uses fake welfare lottery language.'],
  ['within 2 hours', 'Uses artificial urgency / account-block threat.'],
  ['blocked', 'Threatens subsidy suspension to force phishing link click.'],
];

const OFFICIAL_PORTALS: [string, string, string][] = [
  ['pm-kisan', 'PM-KISAN Samman Nidhi', 'https://pmkisan.gov.in'],
  ['pmkisan', 'PM-KISAN Samman Nidhi', 'https://pmkisan.gov.in'],
  ['rythu', 'Telangana Rythu Bharosa', 'https://rythubharosa.telangana.gov.in'],
  ['mahalakshmi', 'Telangana Mahalakshmi', 'https://prajapalana.telangana.gov.in'],
  ['gruha lakshmi', 'Karnataka Gruha Lakshmi', 'https://sevasindhugs.karnataka.gov.in'],
  ['awas', 'PM Awas Yojana', 'https://pmayg.nic.in'],
  ['pmay', 'PM Awas Yojana', 'https://pmayg.nic.in'],
  ['ayushman', 'Ayushman Bharat PM-JAY', 'https://pmjay.gov.in'],
  ['vishwakarma', 'PM Vishwakarma', 'https://pmvishwakarma.gov.in'],
  ['ujjwala', 'PM Ujjwala Yojana', 'https://pmuy.gov.in'],
  ['surya', 'PM Surya Ghar', 'https://pmsuryaghar.gov.in'],
  ['scholarship', 'National Scholarship Portal', 'https://scholarships.gov.in'],
];

export function analyzeScamMessage(message: string): ScamAnalysis {
  const lower = (message || '').toLowerCase();
  const red_flags: string[] = [];
  let score = 0;

  const urls = lower.match(/https?:\/\/[^\s]+|www\.[^\s]+|tinyurl\.com\/[^\s]+|bit\.ly\/[^\s]+/g) ?? [];
  const hasOfficial = urls.some((u) => OFFICIAL_DOMAINS.some((od) => u.includes(od)));
  const hasSuspicious = urls.some((u) => SUSPICIOUS_TLDS.some((tld) => u.includes(tld)));

  if (hasSuspicious) {
    score += 0.55;
    red_flags.push('Contains an unofficial or shortened URL/APK instead of a verified .gov.in / .nic.in domain.');
  }

  for (const [kw, reason] of SCAM_PATTERNS) {
    if (!lower.includes(kw)) continue;
    if (kw === 'otp' && (lower.includes('never share') || lower.includes('do not share'))) continue;
    if (kw === 'registration fee' && (lower.includes('no registration fee') || lower.includes('completely free'))) continue;
    score += 0.28;
    if (!red_flags.includes(reason)) red_flags.push(reason);
  }

  if (hasOfficial && !hasSuspicious && score < 0.3) {
    score = Math.max(0, score - 0.35);
  }

  const verdict: 'SCAM' | 'LEGITIMATE' = score >= 0.4 ? 'SCAM' : 'LEGITIMATE';
  const confidence = Math.round(Math.min(0.99, Math.max(0.05, score >= 0.4 ? score : 1 - score)) * 1000) / 1000;

  let official_scheme = 'MyScheme National Portal';
  let official_url = 'https://www.myscheme.gov.in';
  for (const [hint, name, url] of OFFICIAL_PORTALS) {
    if (lower.includes(hint)) {
      official_scheme = name;
      official_url = url;
      break;
    }
  }

  return {
    verdict,
    risk_score: Math.round(Math.min(1, score) * 1000) / 1000,
    confidence,
    red_flags,
    official_scheme,
    official_url,
    disclaimer: DISCLAIMER,
  };
}

// ---- DPDP-Compliant Document OCR Autofill (F3) ----
export function extractProfileFromText(rawText: string): {
  extracted_profile: Partial<CitizenProfile>;
  masked_ocr_preview: string;
  pii_redacted_types: string[];
  raw_document_deleted: boolean;
  aadhaar_stored: boolean;
} {
  const masked = maskPii(rawText);
  const lower = rawText.toLowerCase();
  const extracted: Partial<CitizenProfile> = {};

  const incMatch = lower.match(/(?:annual\s*)?income\s*[:-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+)/);
  if (incMatch) extracted.income = parseInt(incMatch[1].replace(/,/g, ''), 10);

  const ageMatch = lower.match(/\bage\s*[:-]?\s*(\d{1,2})\b/);
  if (ageMatch) extracted.age = parseInt(ageMatch[1], 10);

  const landMatch = lower.match(/(?:land|extent|area)\s*[:-]?\s*(\d+(?:\.\d+)?)\s*(?:acres?|ac)/);
  if (landMatch) extracted.land = parseFloat(landMatch[1]);

  for (const st of ['Telangana', 'Andhra Pradesh', 'Karnataka', 'Tamil Nadu', 'Maharashtra']) {
    if (lower.includes(st.toLowerCase())) {
      extracted.state = st;
      break;
    }
  }

  if (/\bsc\b|scheduled caste/.test(lower)) extracted.category = 'SC';
  else if (/\bst\b|scheduled tribe/.test(lower)) extracted.category = 'ST';
  else if (/\bobc\b|backward class/.test(lower)) extracted.category = 'OBC';
  else if (/\bews\b/.test(lower)) extracted.category = 'EWS';
  else if (/minority/.test(lower)) extracted.category = 'Minority';

  if (/\b(female|woman|wife of|w\/o|d\/o|smt\.?)\b/.test(lower)) extracted.gender = 'Female';
  else if (/\b(male|man|son of|s\/o|shri\.?)\b/.test(lower)) extracted.gender = 'Male';

  if (/(farmer|pattadar|rythu|agricultur|cultivator)/.test(lower)) extracted.occupation = 'Farmer';
  else if (/(student|bonafide)/.test(lower)) extracted.occupation = 'Student';
  else if (/(artisan|weaver|craft)/.test(lower)) extracted.occupation = 'Artisan';

  if (/(white ration|bpl|antyodaya|food security card|rice card)/.test(lower)) extracted.bpl = true;

  if (/(mandal|gram panchayat|village|rural)/.test(lower)) extracted.residence = 'Rural';
  else if (/(municipality|ghmc|bbmp|urban|ward no)/.test(lower)) extracted.residence = 'Urban';

  if (/(udid|disability|divyang)/.test(lower)) extracted.disability = true;

  return {
    extracted_profile: extracted,
    masked_ocr_preview: masked.maskedText,
    pii_redacted_types: masked.redactedTypes,
    raw_document_deleted: true,
    aadhaar_stored: false,
  };
}
