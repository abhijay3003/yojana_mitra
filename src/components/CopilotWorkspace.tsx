import React, { useEffect, useRef, useState } from 'react';
import {
  Check,
  CheckCircle2,
  Copy,
  ExternalLink,
  HelpCircle,
  Loader2,
  MessageCircle,
  Mic,
  MicOff,
  Send,
  ShieldAlert,
  Square,
  ThumbsDown,
  ThumbsUp,
  Volume2,
  XCircle,
} from 'lucide-react';
import type {
  CitizenProfile,
  CopilotQueryResponse,
  LanguageCode,
  RuleEvaluation,
  CounterfactualResult,
  RejectionPrediction,
} from '../lib/types';
import {
  buildWhatsAppShareUrl,
  formatCopilotShareText,
  formatSingleVerdictShareText,
  isTtsSupported,
  speakText,
  startVoiceInput,
  stopSpeaking,
  type VoiceCaptureHandle,
} from '../lib/voiceAndShare';

interface Props {
  profile: CitizenProfile;
  onProfileChange: (next: CitizenProfile) => void;
  lang: LanguageCode;
  onLangChange: (lang: LanguageCode) => void;
  subTab: 'copilot' | 'wizard';
  onSubTabChange: (tab: 'copilot' | 'wizard') => void;
  consentGiven: boolean;
  onRequestConsent: () => void;
  copilotResult: CopilotQueryResponse | null;
  onSubmitQuery: (query: string) => Promise<void>;
  loading: boolean;
  wizardEvals: RuleEvaluation[];
  wizardCounterfactuals: CounterfactualResult[];
  wizardRejectionRisks: RejectionPrediction[];
  totalEligible: number;
  totalSchemes: number;
  optimalStackInr: number;
  onRunWizard: () => Promise<void>;
}

const LANGUAGES: { code: LanguageCode; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
  { code: 'ta', label: 'தமிழ்' },
];

const QUICK_PROMPTS: { label: string; lang: LanguageCode; query: string }[] = [
  {
    label: 'Telugu Farmer Query',
    lang: 'te',
    query: 'నేను తెలంగాణ ఎస్సీ మహిళా రైతును, 2 ఎకరాల భూమి ఉంది. నాకు ఏ సంక్షేమ పథకాలు వర్తిస్తాయి?',
  },
  {
    label: 'Hindi PM-KISAN + Ujjwala',
    lang: 'hi',
    query: 'पीएम किसान सम्मान निधि और उज्ज्वला योजना की पात्रता और दस्तावेज क्या हैं?',
  },
  {
    label: 'Kannada Gruha Lakshmi',
    lang: 'kn',
    query: 'ಗೃಹ ಲಕ್ಷ್ಮಿ ಯೋಜನೆ ಮತ್ತು ಗೃಹ ಜ್ಯೋತಿ ಅರ್ಹತೆ ಏನು?',
  },
  {
    label: 'Tamil Magalir Urimai',
    lang: 'ta',
    query: 'கலைஞர் மகளிர் உரிமைத் தொகை தகுதி மற்றும் ஆவணங்கள் என்ன?',
  },
  {
    label: 'PII Redaction Test',
    lang: 'en',
    query: 'My name is Lakshmi Devi, Aadhaar 2345 6789 0123, phone 9876543210. Am I eligible for Rythu Bharosa and Mahalakshmi?',
  },
];

export const CopilotWorkspace: React.FC<Props> = ({
  profile,
  onProfileChange,
  lang,
  onLangChange,
  subTab,
  onSubTabChange,
  consentGiven,
  onRequestConsent,
  copilotResult,
  onSubmitQuery,
  loading,
  wizardEvals,
  wizardCounterfactuals,
  wizardRejectionRisks,
  totalEligible,
  totalSchemes,
  optimalStackInr,
  onRunWizard,
}) => {
  const [query, setQuery] = useState(QUICK_PROMPTS[0].query);
  const [selectedEvalId, setSelectedEvalId] = useState<string>('');
  const [feedbackSent, setFeedbackSent] = useState<'up' | 'down' | null>(null);
  const [listening, setListening] = useState(false);
  const [voiceNotice, setVoiceNotice] = useState<string | null>(null);
  const [speaking, setSpeaking] = useState(false);
  const [copied, setCopied] = useState(false);
  const voiceHandleRef = useRef<VoiceCaptureHandle | null>(null);

  useEffect(() => {
    return () => {
      voiceHandleRef.current?.stop();
      stopSpeaking();
    };
  }, []);

  const activeEvals = copilotResult?.evaluations?.length ? copilotResult.evaluations : wizardEvals;
  const activeCounterfactuals = copilotResult?.counterfactuals?.length
    ? copilotResult.counterfactuals
    : wizardCounterfactuals;
  const activeRisks = copilotResult?.rejection_risks?.length
    ? copilotResult.rejection_risks
    : wizardRejectionRisks;

  const selectedEval =
    activeEvals.find((e) => e.scheme_id === selectedEvalId) ?? activeEvals[0] ?? null;

  const handleToggleMic = async () => {
    if (listening) {
      voiceHandleRef.current?.stop();
      voiceHandleRef.current = null;
      setListening(false);
      return;
    }
    setVoiceNotice(null);
    stopSpeaking();
    setSpeaking(false);
    setListening(true);
    const handle = await startVoiceInput({
      lang,
      onInterim: (text) => setQuery(text),
      onFinal: (text) => setQuery(text),
      onEnd: () => {
        setListening(false);
        voiceHandleRef.current = null;
      },
      onError: (msg) => {
        setVoiceNotice(msg);
        setListening(false);
        voiceHandleRef.current = null;
      },
    });
    if (handle) {
      voiceHandleRef.current = handle;
      setVoiceNotice(
        handle.mode === 'browser_speech'
          ? `Listening in ${LANGUAGES.find((l) => l.code === lang)?.label ?? 'English'} (free browser mic)...`
          : 'Recording audio clip... tap Stop when finished.'
      );
    }
  };

  const handleToggleSpeak = () => {
    if (!copilotResult) return;
    if (speaking) {
      stopSpeaking();
      setSpeaking(false);
      return;
    }
    setVoiceNotice(null);
    speakText(copilotResult.answer, copilotResult.lang || lang, {
      onStart: () => setSpeaking(true),
      onEnd: () => setSpeaking(false),
      onError: (msg) => {
        setVoiceNotice(msg);
        setSpeaking(false);
      },
    });
  };

  const handleCopySummary = async () => {
    if (!copilotResult) return;
    const text = formatCopilotShareText(copilotResult, selectedEval);
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore clipboard restriction
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    voiceHandleRef.current?.stop();
    setListening(false);
    setVoiceNotice(null);
    stopSpeaking();
    setSpeaking(false);
    setFeedbackSent(null);
    await onSubmitQuery(query);
  };

  const handleFeedback = async (rating: 1 | -1) => {
    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: copilotResult?.safe_query || query,
          schemeId: copilotResult?.retrieved_schemes?.[0]?.scheme_id || '',
          lang,
          rating,
          comment: rating < 0 ? 'User marked answer inaccurate for hard-negative mining' : 'Helpful grounded verdict',
        }),
      });
      setFeedbackSent(rating > 0 ? 'up' : 'down');
    } catch {
      // ignore network error
    }
  };

  return (
    <div className="space-y-5">
      {/* Executive Snapshot KPI Strip */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div className="surface-card px-4 py-3.5">
          <div className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
            Eligible Schemes
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="font-mono-num text-xl font-bold text-slate-900">{totalEligible}</span>
            <span className="font-mono-num text-xs text-slate-500">/ {totalSchemes} screened</span>
          </div>
        </div>
        <div className="surface-card px-4 py-3.5">
          <div className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
            Optimal Annual Stack
          </div>
          <div className="mt-1 font-mono-num text-xl font-bold text-emerald-700">
            ₹{optimalStackInr.toLocaleString('en-IN')}
          </div>
        </div>
        <div className="surface-card px-4 py-3.5">
          <div className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
            Citizen Profile
          </div>
          <div className="mt-1 text-sm font-semibold text-slate-900 truncate">
            {profile.state} · {profile.category} {profile.occupation}
          </div>
        </div>
        <div className="surface-card px-4 py-3.5">
          <div className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
            Decision Engine
          </div>
          <div className="mt-1 text-sm font-semibold text-[#0F294A]">
            Deterministic 10-Field Logic
          </div>
        </div>
      </div>

      {/* Mode Switcher Bar (Clean, No Duplicate Nav or Demo Buttons) */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="inline-flex items-center rounded-lg border border-slate-200 bg-white p-1 shadow-2xs">
          <button
            type="button"
            onClick={() => onSubTabChange('copilot')}
            className={`rounded-md px-3.5 py-1.5 text-xs font-semibold transition-colors whitespace-nowrap ${
              subTab === 'copilot'
                ? 'bg-[#0F294A] text-white'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Ask Copilot
          </button>
          <button
            type="button"
            onClick={() => onSubTabChange('wizard')}
            className={`rounded-md px-3.5 py-1.5 text-xs font-semibold transition-colors whitespace-nowrap ${
              subTab === 'wizard'
                ? 'bg-[#0F294A] text-white'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            6-Question Profile Wizard
          </button>
        </div>

        <span className="text-xs text-slate-500">
          Response language:{' '}
          <strong className="font-semibold text-slate-800">
            {LANGUAGES.find((l) => l.code === lang)?.label ?? 'English'}
          </strong>
        </span>
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
        {/* Left Column: Chat or 6-Question Wizard */}
        <div className="lg:col-span-7 space-y-5">
          {subTab === 'copilot' ? (
            <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
              <div>
                <h2 className="text-base font-semibold text-slate-900">
                  Neurosymbolic Welfare Copilot
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Eligibility verdicts are computed strictly by the deterministic 10-field rule engine. The language model explains verdicts and official steps without deciding eligibility.
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                {QUICK_PROMPTS.map((preset) => (
                  <button
                    key={preset.label}
                    type="button"
                    onClick={() => {
                      onLangChange(preset.lang);
                      setQuery(preset.query);
                    }}
                    className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-800 transition-colors whitespace-nowrap"
                  >
                    {preset.label}
                  </button>
                ))}
              </div>

              <form onSubmit={handleSend} className="space-y-3">
                <label htmlFor="copilot-query" className="sr-only">
                  Ask a welfare scheme question
                </label>
                <textarea
                  id="copilot-query"
                  rows={3}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask in English, Telugu, Hindi, Kannada, or Tamil..."
                  className="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="text-xs text-slate-500">
                    Active profile: {profile.state} · {profile.category} · {profile.gender} · {profile.occupation} · ₹{profile.income.toLocaleString('en-IN')}/yr · {profile.land} ac
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => void handleToggleMic()}
                      disabled={loading}
                      title={`Voice input (${LANGUAGES.find((l) => l.code === lang)?.label ?? 'English'})`}
                      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors whitespace-nowrap shrink-0 ${
                        listening
                          ? 'border-red-400 bg-red-50 text-red-700 hover:bg-red-100'
                          : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      {listening ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
                      {listening ? 'Stop Mic' : 'Voice Mic'}
                    </button>
                    <button
                      type="submit"
                      disabled={loading || !query.trim()}
                      className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 disabled:opacity-50 transition-colors whitespace-nowrap shrink-0"
                    >
                      {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                      Run Agent Pipeline
                    </button>
                  </div>
                </div>
                {voiceNotice && (
                  <p className="text-xs text-slate-600" role="status">
                    {voiceNotice}
                  </p>
                )}
              </form>

              {/* Copilot Synthesized Grounded Response */}
              {copilotResult && (
                <div className="border-t border-slate-200 pt-4 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-slate-800">Intent: {copilotResult.intent}</span>
                      <span aria-hidden="true">·</span>
                      <span>Language: {copilotResult.lang.toUpperCase()}</span>
                      <span aria-hidden="true">·</span>
                      <span>Retriever: {copilotResult.retriever_mode}</span>
                      <span aria-hidden="true">·</span>
                      <span className="font-mono-num">Faithfulness: {copilotResult.faithfulness}</span>
                      <span aria-hidden="true">·</span>
                      <span className="font-mono-num">{copilotResult.latency_ms} ms</span>
                    </div>

                    {/* Free Browser TTS + DPDP-Safe WhatsApp Share */}
                    <div className="flex flex-wrap items-center gap-2">
                      {isTtsSupported() && (
                        <button
                          type="button"
                          onClick={handleToggleSpeak}
                          className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-semibold transition-colors whitespace-nowrap ${
                            speaking
                              ? 'border-blue-300 bg-blue-50 text-blue-800'
                              : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                          }`}
                        >
                          {speaking ? <Square className="h-3 w-3" /> : <Volume2 className="h-3.5 w-3.5" />}
                          {speaking ? 'Stop Audio' : 'Read Aloud'}
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => void handleCopySummary()}
                        className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors whitespace-nowrap"
                      >
                        {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                        {copied ? 'Copied' : 'Copy'}
                      </button>
                      <a
                        href={buildWhatsAppShareUrl(formatCopilotShareText(copilotResult, selectedEval))}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 rounded-md bg-emerald-700 px-2.5 py-1 text-xs font-semibold text-white hover:bg-emerald-800 transition-colors whitespace-nowrap"
                      >
                        <MessageCircle className="h-3.5 w-3.5" />
                        WhatsApp Share
                      </a>
                    </div>
                  </div>

                  {copilotResult.pii_redacted.length > 0 && (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-xs text-amber-900">
                      <span className="font-semibold">DPDP PII Masker Active:</span> Redacted{' '}
                      <span className="font-mono-num">{copilotResult.pii_redacted.join(', ')}</span> before logging and model inference.
                      <div className="mt-1 font-mono-num text-[11px] text-amber-800">
                        Sanitized query: {copilotResult.safe_query}
                      </div>
                    </div>
                  )}

                  <div className="rounded-lg bg-slate-50 p-4 text-sm leading-relaxed text-slate-800 whitespace-pre-line">
                    {copilotResult.answer}
                  </div>

                  {/* F8 Feedback Loop */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-1 text-xs text-slate-500">
                    <span>
                      {copilotResult.llm_used
                        ? 'Explained by Gemini (grounded on deterministic rule trace)'
                        : 'Grounded deterministic explanation (cached mode)'}
                    </span>
                    <div className="flex items-center gap-2">
                      <span>Was this accurate?</span>
                      <button
                        type="button"
                        onClick={() => void handleFeedback(1)}
                        className={`inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                          feedbackSent === 'up'
                            ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
                            : 'border-slate-200 text-slate-600 hover:bg-slate-100'
                        }`}
                      >
                        <ThumbsUp className="h-3.5 w-3.5" /> Yes
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleFeedback(-1)}
                        className={`inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                          feedbackSent === 'down'
                            ? 'border-red-300 bg-red-50 text-red-800'
                            : 'border-slate-200 text-slate-600 hover:bg-slate-100'
                        }`}
                      >
                        <ThumbsDown className="h-3.5 w-3.5" /> Flag
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* F9: 6-Question Eligibility Wizard */
            <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-5">
              <div>
                <h2 className="text-base font-semibold text-slate-900">
                  6-Question Citizen Eligibility Wizard
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Adjust the citizen profile below to deterministically evaluate all 113 Central and State welfare schemes in real time.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">1. State of Residence</label>
                  <select
                    value={profile.state}
                    onChange={(e) => onProfileChange({ ...profile, state: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
                  >
                    <option value="Telangana">Telangana</option>
                    <option value="Andhra Pradesh">Andhra Pradesh</option>
                    <option value="Karnataka">Karnataka</option>
                    <option value="Tamil Nadu">Tamil Nadu</option>
                    <option value="Maharashtra">Maharashtra</option>
                    <option value="Other">Other State</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">2. Social Category & Gender</label>
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={profile.category}
                      onChange={(e) =>
                        onProfileChange({ ...profile, category: e.target.value as CitizenProfile['category'] })
                      }
                      className="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-sm text-slate-900"
                    >
                      <option value="SC">SC</option>
                      <option value="ST">ST</option>
                      <option value="OBC">OBC</option>
                      <option value="EWS">EWS</option>
                      <option value="Minority">Minority</option>
                      <option value="GEN">GEN</option>
                    </select>
                    <select
                      value={profile.gender}
                      onChange={(e) =>
                        onProfileChange({ ...profile, gender: e.target.value as CitizenProfile['gender'] })
                      }
                      className="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-sm text-slate-900"
                    >
                      <option value="Female">Female</option>
                      <option value="Male">Male</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">3. Occupation & Area</label>
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={profile.occupation}
                      onChange={(e) =>
                        onProfileChange({ ...profile, occupation: e.target.value as CitizenProfile['occupation'] })
                      }
                      className="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-sm text-slate-900"
                    >
                      <option value="Farmer">Farmer</option>
                      <option value="Agricultural Laborer">Agri Laborer</option>
                      <option value="Student">Student</option>
                      <option value="Artisan">Artisan</option>
                      <option value="Self-Employed">Self-Employed</option>
                      <option value="Unemployed">Unemployed</option>
                      <option value="Salaried">Salaried</option>
                    </select>
                    <select
                      value={profile.residence}
                      onChange={(e) =>
                        onProfileChange({ ...profile, residence: e.target.value as CitizenProfile['residence'] })
                      }
                      className="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-sm text-slate-900"
                    >
                      <option value="Rural">Rural</option>
                      <option value="Urban">Urban</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">4. Age (Years)</label>
                  <input
                    type="number"
                    min={0}
                    max={110}
                    value={profile.age}
                    onChange={(e) => onProfileChange({ ...profile, age: Number(e.target.value) })}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-mono-num text-slate-900"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">5. Annual Family Income (₹)</label>
                  <input
                    type="number"
                    min={0}
                    step={10000}
                    value={profile.income}
                    onChange={(e) => onProfileChange({ ...profile, income: Number(e.target.value) })}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-mono-num text-slate-900"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">6. Land Holding (Acres) & Cards</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="number"
                      min={0}
                      step={0.5}
                      value={profile.land}
                      onChange={(e) => onProfileChange({ ...profile, land: Number(e.target.value) })}
                      className="w-24 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-mono-num text-slate-900"
                    />
                    <label className="inline-flex items-center gap-1.5 text-xs text-slate-700">
                      <input
                        type="checkbox"
                        checked={profile.bpl}
                        onChange={(e) => onProfileChange({ ...profile, bpl: e.target.checked })}
                        className="rounded border-slate-300 text-blue-700"
                      />
                      BPL / White Ration
                    </label>
                    <label className="inline-flex items-center gap-1.5 text-xs text-slate-700">
                      <input
                        type="checkbox"
                        checked={profile.disability}
                        onChange={(e) => onProfileChange({ ...profile, disability: e.target.checked })}
                        className="rounded border-slate-300 text-blue-700"
                      />
                      Divyang
                    </label>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-slate-200 pt-4">
                <span className="text-xs text-slate-600">
                  Deterministic matches found: <strong className="font-mono-num text-slate-900">{totalEligible}</strong> eligible schemes
                </span>
                <button
                  type="button"
                  onClick={() => void onRunWizard()}
                  disabled={loading}
                  className="rounded-lg bg-blue-700 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-800 transition-colors whitespace-nowrap"
                >
                  Re-Evaluate All 113 Schemes
                </button>
              </div>
            </div>
          )}

          {/* Live Agent Pipeline Execution Trace (P6) */}
          {copilotResult && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">Agentic Execution Trace (PII-Masked)</h3>
                <span className="font-mono-num text-xs text-slate-500">
                  Total {copilotResult.latency_ms} ms
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500">
                      <th className="py-2 pr-4 font-medium">Graph Node</th>
                      <th className="py-2 pr-4 font-medium">Output Summary</th>
                      <th className="py-2 text-right font-medium">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {copilotResult.spans.map((span, idx) => (
                      <tr key={`${span.node}-${idx}`} className="hover:bg-slate-50">
                        <td className="py-2 pr-4 font-mono-num font-medium text-slate-800">{span.node}</td>
                        <td className="py-2 pr-4 text-slate-600">{span.summary}</td>
                        <td className="py-2 text-right font-mono-num text-slate-700">{span.latency_ms} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Deterministic Rule Trace + Counterfactual "Why Not" + Rejection Risk */}
        <div className="lg:col-span-5 space-y-5">
          {/* Ranked Schemes & Deterministic Rule Trace */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">Deterministic Rule Trace</h3>
              <span className="text-xs text-slate-500">Click scheme to inspect</span>
            </div>

            {!consentGiven && (
              <div className="flex items-center justify-between gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-900">
                <span>Accept DPDP Act 2023 notice to save alerts or scan docs.</span>
                <button
                  type="button"
                  onClick={onRequestConsent}
                  className="font-semibold text-blue-700 underline whitespace-nowrap"
                >
                  Accept
                </button>
              </div>
            )}

            <div className="divide-y divide-slate-100 max-h-64 overflow-y-auto">
              {activeEvals.slice(0, 8).map((ev) => {
                const isSelected = selectedEval?.scheme_id === ev.scheme_id;
                return (
                  <button
                    key={ev.scheme_id}
                    type="button"
                    onClick={() => setSelectedEvalId(ev.scheme_id)}
                    className={`w-full py-2.5 px-2 text-left transition-colors flex items-center justify-between gap-3 ${
                      isSelected ? 'bg-blue-50/70' : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="min-w-0">
                      <div className="truncate text-xs font-semibold text-slate-900">{ev.scheme_name}</div>
                      <div className="text-[11px] text-slate-500">
                        {ev.state} · Match <span className="font-mono-num">{ev.match_score}%</span> ·{' '}
                        <span className="font-mono-num">₹{ev.annual_benefit_inr.toLocaleString('en-IN')}/yr</span>
                      </div>
                    </div>
                    <span
                      className={`inline-flex items-center gap-1 text-xs font-semibold shrink-0 ${
                        ev.verdict === 'ELIGIBLE'
                          ? 'text-emerald-700'
                          : ev.verdict === 'NEEDS_INFO'
                            ? 'text-amber-700'
                            : 'text-red-700'
                      }`}
                    >
                      {ev.verdict === 'ELIGIBLE' ? (
                        <CheckCircle2 className="h-3.5 w-3.5" />
                      ) : ev.verdict === 'NEEDS_INFO' ? (
                        <HelpCircle className="h-3.5 w-3.5" />
                      ) : (
                        <XCircle className="h-3.5 w-3.5" />
                      )}
                      {ev.verdict.replace('_', ' ')}
                    </span>
                  </button>
                );
              })}
            </div>

            {selectedEval && (
              <div className="border-t border-slate-200 pt-3 space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-slate-900">{selectedEval.scheme_name}</span>
                  <div className="flex items-center gap-3">
                    <a
                      href={buildWhatsAppShareUrl(formatSingleVerdictShareText(selectedEval))}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 hover:underline whitespace-nowrap"
                    >
                      <MessageCircle className="h-3 w-3" /> Share Verdict
                    </a>
                    <a
                      href={selectedEval.apply_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:underline whitespace-nowrap"
                    >
                      Official Portal <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
                <ul className="space-y-1.5 text-xs">
                  {selectedEval.passed.map((p, idx) => (
                    <li key={`p-${idx}`} className="flex items-start gap-2 text-emerald-800">
                      <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0 text-emerald-600" />
                      <span>
                        {p.label} <span className="font-mono-num text-slate-500">({String(p.actual)})</span>
                      </span>
                    </li>
                  ))}
                  {selectedEval.failed.map((f, idx) => (
                    <li key={`f-${idx}`} className="flex items-start gap-2 text-red-800">
                      <XCircle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-red-600" />
                      <span>
                        {f.label}{' '}
                        <span className="font-mono-num text-red-600">
                          (yours: {String(f.actual)}, required {f.op} {String(f.expected)})
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* F2: Counterfactual "Why Not" Panel */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Counterfactual &ldquo;Why Not&rdquo; Analysis</h3>
              <p className="text-xs text-slate-500">
                Minimal profile change required to flip a non-eligible scheme verdict to ELIGIBLE (100% engine-verified).
              </p>
            </div>
            {activeCounterfactuals.length === 0 ? (
              <p className="text-xs text-slate-500">All displayed top schemes are already eligible for this profile.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {activeCounterfactuals.slice(0, 3).map((cf) => (
                  <div key={cf.scheme_id} className="py-2.5 space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-semibold text-slate-900">{cf.scheme_name}</span>
                      <span className="font-mono-num text-[11px] text-emerald-700">
                        {cf.verified_eligible ? 'Verified Flip' : 'Constrained'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600">{cf.summary}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* F7: Rejection Risk Predictor Snapshot */}
          {activeRisks.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">Top Rejection Risk Factors</h3>
                <span className="font-mono-num text-xs font-semibold text-amber-700">
                  {activeRisks[0].risk_band} · {Math.round(activeRisks[0].rejection_probability * 100)}%
                </span>
              </div>
              <p className="text-xs text-slate-500">For {activeRisks[0].scheme_name}</p>
              <ol className="space-y-2 text-xs">
                {activeRisks[0].top_3_reasons.map((item, idx) => (
                  <li key={idx} className="space-y-0.5">
                    <div className="flex items-start gap-2 font-medium text-slate-800">
                      <ShieldAlert className="h-3.5 w-3.5 mt-0.5 shrink-0 text-amber-600" />
                      <span>{item.reason}</span>
                    </div>
                    <div className="pl-5 text-slate-500">Fix: {item.mitigation}</div>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
