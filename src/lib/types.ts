export type LanguageCode = 'en' | 'te' | 'hi' | 'kn' | 'ta';

export type Verdict = 'ELIGIBLE' | 'NOT_ELIGIBLE' | 'NEEDS_INFO';

export interface RulePredicate {
  field:
    | 'age'
    | 'income'
    | 'state'
    | 'category'
    | 'gender'
    | 'occupation'
    | 'land'
    | 'disability'
    | 'bpl'
    | 'residence';
  op: '==' | '!=' | '<=' | '>=' | '<' | '>' | 'in' | 'not_in';
  value: string | number | boolean | string[];
  label?: string;
}

export interface Scheme {
  scheme_id: string;
  name: string;
  ministry: string;
  state: string;
  category: string;
  benefits: string;
  annual_benefit_inr: number;
  eligibility_text: string;
  rules: RulePredicate[];
  documents: string[];
  apply_url: string;
  source_url: string;
  last_updated: string;
  lang: string;
  translations?: Record<string, string>;
  keywords?: string[];
  mutually_exclusive_with?: string[];
  complementary_to?: string[];
  supersedes?: string[];
  sub_scheme_of?: string | null;
}

export interface CitizenProfile {
  age: number;
  income: number;
  state: string;
  category: 'SC' | 'ST' | 'OBC' | 'GEN' | 'EWS' | 'Minority';
  gender: 'Female' | 'Male' | 'Other';
  occupation:
    | 'Farmer'
    | 'Agricultural Laborer'
    | 'Student'
    | 'Artisan'
    | 'Self-Employed'
    | 'Salaried'
    | 'Unemployed'
    | 'Retired';
  land: number;
  disability: boolean;
  bpl: boolean;
  residence: 'Rural' | 'Urban';
}

export interface RuleCheckEntry {
  field: string;
  op: string;
  expected: unknown;
  actual: unknown;
  label: string;
  status: 'PASS' | 'FAIL' | 'MISSING';
}

export interface RuleEvaluation {
  scheme_id: string;
  scheme_name: string;
  verdict: Verdict;
  passed: RuleCheckEntry[];
  failed: RuleCheckEntry[];
  missing: RuleCheckEntry[];
  trace: string[];
  match_score: number;
  annual_benefit_inr: number;
  state: string;
  category: string;
  apply_url: string;
  documents: string[];
}

export interface CounterfactualChange {
  field: string;
  op: string;
  current: unknown;
  required: unknown;
  suggested_value: unknown;
  actionable: boolean;
  explanation: string;
}

export interface CounterfactualResult {
  scheme_id: string;
  scheme_name: string;
  already_eligible: boolean;
  changes: CounterfactualChange[];
  summary: string;
  verified_eligible: boolean;
}

export interface StackOptimizationResult {
  solver: string;
  eligible_count: number;
  selected_schemes: {
    scheme_id: string;
    name: string;
    state: string;
    category: string;
    annual_benefit_inr: number;
    apply_url: string;
    documents: string[];
  }[];
  total_annual_inr: number;
  naive_top1_inr: number;
  gain_vs_top1_inr: number;
  gain_vs_top1_pct: number;
  excluded_by_conflict: {
    scheme_id: string;
    name: string;
    conflicts_with: string;
  }[];
}

export interface RejectionPrediction {
  scheme_id: string;
  scheme_name: string;
  verdict: Verdict;
  rejection_probability: number;
  risk_band: 'LOW' | 'MEDIUM' | 'HIGH';
  top_3_reasons: {
    impact_score: number;
    reason: string;
    mitigation: string;
  }[];
}

export interface ScamAnalysis {
  verdict: 'SCAM' | 'LEGITIMATE';
  risk_score: number;
  confidence: number;
  red_flags: string[];
  official_scheme: string;
  official_url: string;
  llm_explanation?: string;
  disclaimer: string;
}

export interface TraceSpan {
  node: string;
  latency_ms: number;
  summary: string;
  status: 'ok' | 'retried' | 'masked';
}

export interface CopilotQueryResponse {
  trace_id: string;
  intent: string;
  lang: LanguageCode;
  retriever_mode: 'vector' | 'graph' | 'none';
  safe_query: string;
  pii_redacted: string[];
  answer: string;
  llm_used: boolean;
  llm_error?: string;
  faithfulness: number;
  retrieved_schemes: Scheme[];
  graph_paths: string[];
  evaluations: RuleEvaluation[];
  counterfactuals: CounterfactualResult[];
  rejection_risks: RejectionPrediction[];
  benefit_stack: StackOptimizationResult | null;
  scam_analysis?: ScamAnalysis;
  latency_ms: number;
  spans: TraceSpan[];
  disclaimer: string;
}

export interface GraphNodeView {
  id: string;
  type: 'Scheme' | 'Ministry' | 'State' | 'BeneficiaryCategory' | 'Document' | 'Benefit';
  label: string;
  scheme_id?: string;
  annual_benefit_inr?: number;
}

export interface GraphEdgeView {
  source: string;
  target: string;
  relation: string;
}

export interface EvalReport {
  seed: number;
  total_schemes: number;
  retrieval: {
    ablations: { layer: string; hit_at_5: number; mrr: number; avg_latency_ms: number }[];
    by_language_hit5: Record<string, number>;
  };
  multihop: { graphrag_acc: number; vanilla_rag_acc: number; gain_pts: number };
  rules: {
    verdict_acc: number;
    counterfactual_acc: number;
    avg_stack_gain_pct: number;
    by_category_acc: Record<string, number>;
    by_gender_acc: Record<string, number>;
  };
  scam_and_intent: { scam_f1: number; intent_macro_f1: number };
  e2e_agents: { p50_ms: number; p95_ms: number; p95_sec: number; faithfulness: number };
  ocr_accuracy_pct: number;
  fairness: {
    language_hit5: Record<string, number>;
    language_gap_pts: number;
    language_flag: boolean;
    category_verdict_acc: Record<string, number>;
    category_gap_pts: number;
    category_flag: boolean;
    gender_verdict_acc: Record<string, number>;
    gender_gap_pts: number;
    gender_flag: boolean;
  };
  drift: {
    psi: number;
    threshold: number;
    alert: boolean;
    severity: string;
    shifted_slices: { slice: string; delta_pct_pts: number }[];
  };
  targets: {
    metric: string;
    target: string;
    measured: string;
    status: 'PASS' | 'MISSED';
    notes: string;
  }[];
}
