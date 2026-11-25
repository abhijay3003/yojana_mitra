import React, { useCallback, useEffect, useState } from 'react';
import {
  BarChart3,
  GitBranch,
  Layers,
  Menu,
  MessageSquare,
  PhoneCall,
  Play,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from 'lucide-react';
import type {
  CitizenProfile,
  CopilotQueryResponse,
  CounterfactualResult,
  EvalReport,
  LanguageCode,
  RejectionPrediction,
  RuleEvaluation,
  Scheme,
  StackOptimizationResult,
} from './lib/types';
import { CopilotWorkspace } from './components/CopilotWorkspace';
import { BenefitStackView } from './components/BenefitStackView';
import { GraphExplorerView } from './components/GraphExplorerView';
import { ScamAndDocView } from './components/ScamAndDocView';
import { FieldWorkerAndIvrView } from './components/FieldWorkerAndIvrView';
import { EvalMlopsView } from './components/EvalMlopsView';

type ActiveSection = 'copilot' | 'optimizer' | 'graph' | 'scam_ocr' | 'field_ivr' | 'eval';

const TELANGANA_SC_FARMER_PROFILE: CitizenProfile = {
  age: 38,
  income: 140000,
  state: 'Telangana',
  category: 'SC',
  gender: 'Female',
  occupation: 'Farmer',
  land: 2.0,
  disability: false,
  bpl: true,
  residence: 'Rural',
};

const LANGUAGES: { code: LanguageCode; short: string; label: string }[] = [
  { code: 'en', short: 'EN', label: 'English' },
  { code: 'te', short: 'తెలుగు', label: 'తెలుగు' },
  { code: 'hi', short: 'हिन्दी', label: 'हिन्दी' },
  { code: 'kn', short: 'ಕನ್ನಡ', label: 'ಕನ್ನಡ' },
  { code: 'ta', short: 'தமிழ்', label: 'தமிழ்' },
];

interface NavItem {
  id: ActiveSection;
  label: string;
  subtitle: string;
  group: 'citizen' | 'ops';
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  {
    id: 'copilot',
    label: 'Copilot & Wizard',
    subtitle: 'Multilingual eligibility copilot, deterministic rule trace & counterfactuals',
    group: 'citizen',
    icon: MessageSquare,
  },
  {
    id: 'optimizer',
    label: 'Benefit Optimizer',
    subtitle: 'Maximize annual household welfare across non-conflicting schemes',
    group: 'citizen',
    icon: Layers,
  },
  {
    id: 'graph',
    label: 'Knowledge Graph',
    subtitle: 'Multi-hop GraphRAG across schemes, documents & state ministries',
    group: 'citizen',
    icon: GitBranch,
  },
  {
    id: 'scam_ocr',
    label: 'Scam & Doc Scan',
    subtitle: 'Phishing verification, ephemeral certificate OCR & rejection risk audit',
    group: 'citizen',
    icon: ShieldCheck,
  },
  {
    id: 'field_ivr',
    label: 'Field Worker & IVR',
    subtitle: '50-family batch CSV screening, voice IVR & proactive diff alerts',
    group: 'ops',
    icon: PhoneCall,
  },
  {
    id: 'eval',
    label: 'Eval & MLOps',
    subtitle: 'Reproducible benchmarks, fairness audit & query drift monitoring',
    group: 'ops',
    icon: BarChart3,
  },
];

export default function App() {
  const [section, setSection] = useState<ActiveSection>('copilot');
  const [copilotSubTab, setCopilotSubTab] = useState<'copilot' | 'wizard'>('copilot');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [evalReport, setEvalReport] = useState<EvalReport | null>(null);
  const [feedbackSummary, setFeedbackSummary] = useState({ total: 0, positive: 0, negative: 0 });
  const [disclaimer, setDisclaimer] = useState('Informational only. Verify on the official portal.');

  const [profile, setProfile] = useState<CitizenProfile>(TELANGANA_SC_FARMER_PROFILE);
  const [lang, setLang] = useState<LanguageCode>('te');
  const [consentGiven, setConsentGiven] = useState(false);
  const [maxSchemes, setMaxSchemes] = useState(5);

  const [copilotResult, setCopilotResult] = useState<CopilotQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const [wizardEvals, setWizardEvals] = useState<RuleEvaluation[]>([]);
  const [wizardCounterfactuals, setWizardCounterfactuals] = useState<CounterfactualResult[]>([]);
  const [wizardRejectionRisks, setWizardRejectionRisks] = useState<RejectionPrediction[]>([]);
  const [benefitStack, setBenefitStack] = useState<StackOptimizationResult | null>(null);
  const [totalEligible, setTotalEligible] = useState(0);

  const evaluateProfile = useCallback(
    async (
      prof: CitizenProfile,
      opts?: { maxSchemes?: number; aadhaarSeeded?: boolean; certAgeMonths?: number },
    ) => {
      try {
        const res = await fetch('/api/rules/evaluate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            profile: prof,
            maxSchemes: opts?.maxSchemes ?? maxSchemes,
            aadhaarBankSeeded: opts?.aadhaarSeeded ?? true,
            certificateAgeMonths: opts?.certAgeMonths ?? 6,
          }),
        });
        if (!res.ok) return;
        const data = await res.json();
        setWizardEvals(data.evaluations ?? []);
        setWizardCounterfactuals(data.counterfactuals ?? []);
        setWizardRejectionRisks(data.rejection_risks ?? []);
        setBenefitStack(data.benefit_stack ?? null);
        setTotalEligible(data.total_eligible ?? 0);
      } catch {
        // ignore transient startup network error
      }
    },
    [maxSchemes],
  );

  useEffect(() => {
    const loadBootstrap = async () => {
      try {
        const res = await fetch('/api/bootstrap');
        if (res.ok) {
          const data = await res.json();
          setSchemes(data.schemes ?? []);
          setEvalReport(data.evalReport ?? null);
          if (data.feedbackSummary) setFeedbackSummary(data.feedbackSummary);
          if (data.disclaimer) setDisclaimer(data.disclaimer);
        }
      } catch {
        // ignore
      }
    };
    void loadBootstrap();
    void evaluateProfile(TELANGANA_SC_FARMER_PROFILE);
  }, [evaluateProfile]);

  const handleSubmitQuery = async (
    queryText: string,
    overrideProfile?: CitizenProfile,
    overrideLang?: LanguageCode,
  ) => {
    setLoading(true);
    try {
      const res = await fetch('/api/copilot/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: queryText,
          profile: overrideProfile ?? profile,
          lang: overrideLang ?? lang,
        }),
      });
      if (res.ok) {
        const data = (await res.json()) as CopilotQueryResponse;
        setCopilotResult(data);
        if (data.benefit_stack) setBenefitStack(data.benefit_stack);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRunTelanganaDemo = async () => {
    setSection('copilot');
    setCopilotSubTab('copilot');
    setMobileMenuOpen(false);
    setProfile(TELANGANA_SC_FARMER_PROFILE);
    setLang('te');
    await evaluateProfile(TELANGANA_SC_FARMER_PROFILE);
    await handleSubmitQuery(
      'నేను తెలంగాణ ఎస్సీ మహిళా రైతును, 2 ఎకరాల భూమి ఉంది. నాకు ఏ సంక్షేమ పథకాలు వర్తిస్తాయి?',
      TELANGANA_SC_FARMER_PROFILE,
      'te',
    );
  };

  const handleProfileUpdate = (next: CitizenProfile) => {
    setProfile(next);
    void evaluateProfile(next);
  };

  const handleMaxSchemesChange = (n: number) => {
    setMaxSchemes(n);
    void evaluateProfile(profile, { maxSchemes: n });
  };

  const handleSelectSection = (id: ActiveSection) => {
    setSection(id);
    setMobileMenuOpen(false);
  };

  const activeNav = NAV_ITEMS.find((i) => i.id === section) ?? NAV_ITEMS[0];
  const citizenNav = NAV_ITEMS.filter((i) => i.group === 'citizen');
  const opsNav = NAV_ITEMS.filter((i) => i.group === 'ops');

  const renderSidebarContent = () => (
    <div className="flex h-full flex-col justify-between">
      <div className="space-y-6">
        {/* Brand Identity */}
        <div className="flex items-center justify-between px-2 pt-1">
          <button
            type="button"
            onClick={() => handleSelectSection('copilot')}
            className="flex items-center gap-2.5 text-left"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#0F294A] text-white shrink-0">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                className="h-4 w-4"
                aria-hidden="true"
              >
                <path
                  d="M12 3L4 7v5c0 5.25 3.4 9.74 8 11 4.6-1.26 8-5.75 8-11V7l-8-4z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinejoin="round"
                />
                <path
                  d="M9 12l2 2 4-4"
                  stroke="#F59E0B"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <div className="min-w-0">
              <div className="font-display text-[15px] font-bold leading-tight text-slate-900">
                Yojana Mitra
              </div>
              <div className="text-[11px] font-medium text-slate-500">
                Welfare Eligibility Copilot
              </div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => setMobileMenuOpen(false)}
            className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 md:hidden"
            aria-label="Close navigation"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Single Authoritative Navigation */}
        <nav className="space-y-5" aria-label="Workspace navigation">
          <div>
            <div className="px-2.5 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Citizen Desk
            </div>
            <div className="space-y-0.5">
              {citizenNav.map((item) => {
                const Icon = item.icon;
                const active = section === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleSelectSection(item.id)}
                    className={`w-full flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] transition-colors whitespace-nowrap ${
                      active
                        ? 'bg-[#0F294A] text-white font-semibold shadow-xs'
                        : 'text-slate-600 font-medium hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <Icon className={`h-4 w-4 shrink-0 ${active ? 'text-amber-300' : 'text-slate-400'}`} />
                    <span className="truncate">{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <div className="px-2.5 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Field &amp; Quality
            </div>
            <div className="space-y-0.5">
              {opsNav.map((item) => {
                const Icon = item.icon;
                const active = section === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleSelectSection(item.id)}
                    className={`w-full flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] transition-colors whitespace-nowrap ${
                      active
                        ? 'bg-[#0F294A] text-white font-semibold shadow-xs'
                        : 'text-slate-600 font-medium hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <Icon className={`h-4 w-4 shrink-0 ${active ? 'text-amber-300' : 'text-slate-400'}`} />
                    <span className="truncate">{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </nav>

        {/* Active Citizen Profile Summary */}
        <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-3.5 space-y-2.5 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-800">Active Profile</span>
            <button
              type="button"
              onClick={() => {
                setSection('copilot');
                setCopilotSubTab('wizard');
                setMobileMenuOpen(false);
              }}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-700 hover:underline"
            >
              <SlidersHorizontal className="h-3 w-3" /> Edit
            </button>
          </div>
          <div className="space-y-1.5 text-slate-600">
            <div className="flex justify-between gap-2">
              <span>Jurisdiction</span>
              <span className="font-medium text-slate-900 truncate">{profile.state}</span>
            </div>
            <div className="flex justify-between gap-2">
              <span>Cohort</span>
              <span className="font-medium text-slate-900">
                {profile.category} · {profile.gender}
              </span>
            </div>
            <div className="flex justify-between gap-2">
              <span>Occupation</span>
              <span className="font-medium text-slate-900 truncate">{profile.occupation}</span>
            </div>
            <div className="flex justify-between gap-2">
              <span>Income</span>
              <span className="font-mono-num font-medium text-slate-900">
                ₹{profile.income.toLocaleString('en-IN')}
              </span>
            </div>
            <div className="border-t border-slate-200 pt-1.5 mt-1.5 flex justify-between gap-2">
              <span>Eligible</span>
              <span className="font-mono-num font-semibold text-emerald-700">
                {totalEligible} / {schemes.length || 113}
              </span>
            </div>
            <div className="flex justify-between gap-2">
              <span>Best Stack</span>
              <span className="font-mono-num font-semibold text-blue-700">
                ₹{(benefitStack?.total_annual_inr ?? 0).toLocaleString('en-IN')}/yr
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* DPDP Privacy Footer */}
      <div className="border-t border-slate-200 pt-3.5 px-2 space-y-1 text-[11px] text-slate-500">
        <div className="font-semibold text-slate-700">DPDP Act 2023 Safeguard</div>
        <p className="leading-relaxed">
          Aadhaar, PAN, phone, email, and names are masked before logging or AI explanation.
        </p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex bg-[#f6f7f9] text-slate-900">
      {/* Desktop Persistent Sidebar (Single Source of Navigation) */}
      <aside className="hidden md:flex md:w-64 md:shrink-0 md:flex-col border-r border-slate-200 bg-white p-4 sticky top-0 h-screen overflow-y-auto">
        {renderSidebarContent()}
      </aside>

      {/* Mobile Slide-Over Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-[1px]"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />
          <aside className="relative z-10 flex w-72 max-w-[85vw] flex-col bg-white p-4 shadow-xl overflow-y-auto">
            {renderSidebarContent()}
          </aside>
        </div>
      )}

      {/* Right Main Shell: Clean Context Topbar + Viewport */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur-xs">
          <div className="flex items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8 max-w-[1280px] mx-auto w-full">
            <div className="flex items-center gap-3 min-w-0">
              <button
                type="button"
                onClick={() => setMobileMenuOpen(true)}
                className="inline-flex md:hidden items-center justify-center rounded-lg border border-slate-200 p-2 text-slate-700 hover:bg-slate-50 shrink-0"
                aria-label="Open navigation menu"
              >
                <Menu className="h-4 w-4" />
              </button>
              <div className="min-w-0">
                <h1 className="font-display text-base sm:text-lg font-bold text-slate-900 truncate">
                  {activeNav.label}
                </h1>
                <p className="hidden sm:block text-xs text-slate-500 truncate">
                  {activeNav.subtitle}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 shrink-0">
              {/* Global Language Selector (Single Place) */}
              <div
                className="hidden sm:flex items-center rounded-lg border border-slate-200 bg-slate-50 p-0.5"
                role="group"
                aria-label="Response language"
              >
                {LANGUAGES.map((l) => (
                  <button
                    key={l.code}
                    type="button"
                    onClick={() => setLang(l.code)}
                    className={`rounded-md px-2 py-1 text-xs font-medium transition-colors whitespace-nowrap ${
                      lang === l.code
                        ? 'bg-white text-[#0F294A] font-semibold shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {l.short}
                  </button>
                ))}
              </div>

              <select
                aria-label="Response language"
                value={lang}
                onChange={(e) => setLang(e.target.value as LanguageCode)}
                className="sm:hidden rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs font-medium text-slate-800"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.label}
                  </option>
                ))}
              </select>

              {/* Single Global Primary Demo Action */}
              <button
                type="button"
                onClick={() => void handleRunTelanganaDemo()}
                disabled={loading}
                className="inline-flex items-center gap-1.5 rounded-lg bg-[#0F294A] px-3.5 py-2 text-xs font-semibold text-white hover:bg-[#173b69] disabled:opacity-60 transition-colors whitespace-nowrap shrink-0"
              >
                <Play className="h-3.5 w-3.5 text-amber-300" />
                <span>Telangana Demo</span>
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 px-4 py-5 sm:px-6 lg:px-8 max-w-[1280px] mx-auto w-full space-y-5">
          {section === 'copilot' && (
            <CopilotWorkspace
              profile={profile}
              onProfileChange={handleProfileUpdate}
              lang={lang}
              onLangChange={setLang}
              subTab={copilotSubTab}
              onSubTabChange={setCopilotSubTab}
              consentGiven={consentGiven}
              onRequestConsent={() => setConsentGiven(true)}
              copilotResult={copilotResult}
              onSubmitQuery={(q) => handleSubmitQuery(q)}
              loading={loading}
              wizardEvals={wizardEvals}
              wizardCounterfactuals={wizardCounterfactuals}
              wizardRejectionRisks={wizardRejectionRisks}
              totalEligible={totalEligible}
              totalSchemes={schemes.length || 113}
              optimalStackInr={benefitStack?.total_annual_inr ?? 0}
              onRunWizard={() => evaluateProfile(profile)}
            />
          )}

          {section === 'optimizer' && (
            <BenefitStackView
              profile={profile}
              stack={benefitStack}
              maxSchemes={maxSchemes}
              onMaxSchemesChange={handleMaxSchemesChange}
            />
          )}

          {section === 'graph' && <GraphExplorerView schemes={schemes} />}

          {section === 'scam_ocr' && (
            <ScamAndDocView
              profile={profile}
              onApplyExtractedProfile={(partial) => {
                const merged = { ...profile, ...partial };
                setProfile(merged);
                void evaluateProfile(merged);
                setSection('copilot');
              }}
              consentGiven={consentGiven}
              onGiveConsent={() => setConsentGiven(true)}
              rejectionRisks={wizardRejectionRisks}
              onRefreshRejection={(opts) => evaluateProfile(profile, opts)}
            />
          )}

          {section === 'field_ivr' && <FieldWorkerAndIvrView profile={profile} />}

          {section === 'eval' && (
            <EvalMlopsView evalReport={evalReport} feedbackSummary={feedbackSummary} />
          )}

          {/* Persistent Official Portal Disclaimer Footer */}
          <footer className="border-t border-slate-200 pt-4 pb-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
            <span>{disclaimer}</span>
            <span>Deterministic 10-Field Rule Engine · Zero Aadhaar Storage</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
