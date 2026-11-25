import React, { useEffect, useRef, useState } from 'react';
import {
  Bell,
  Download,
  Loader2,
  MessageCircle,
  Mic,
  MicOff,
  PhoneCall,
  Square,
  Users,
  Volume2,
} from 'lucide-react';
import type { CitizenProfile, LanguageCode } from '../lib/types';
import {
  buildWhatsAppShareUrl,
  speakText,
  startVoiceInput,
  stopSpeaking,
  type VoiceCaptureHandle,
} from '../lib/voiceAndShare';

interface Props {
  profile: CitizenProfile;
}

interface BatchResult {
  families_screened: number;
  aggregate_annual_welfare_inr: number;
  avg_ms_per_family: number;
  total_ms: number;
  results: {
    family_id: string;
    state: string;
    category: string;
    occupation: string;
    eligible_count: number;
    top_stacked_schemes: string;
    total_annual_inr: number;
    gain_vs_top1_pct: number;
  }[];
  csv_output: string;
}

interface IvrResponse {
  stage: string;
  lang: string;
  tts_prompt?: string;
  spoken_response?: string;
  twiml: string;
  sms_summary?: string;
  matched_scheme?: string | null;
  verdict?: string | null;
}

interface AlertItem {
  profile_label: string;
  scheme_id: string;
  scheme_name: string;
  annual_benefit_inr: number;
  apply_url: string;
  whatsapp_preview: string;
}

function generateDemo50FamiliesCsv(): string {
  const header = 'family_id,age,income,state,category,gender,occupation,land,disability,bpl,residence';
  const states = ['Telangana', 'Andhra Pradesh', 'Karnataka', 'Tamil Nadu', 'Telangana'];
  const cats = ['SC', 'ST', 'OBC', 'EWS', 'SC'];
  const occs = ['Farmer', 'Farmer', 'Artisan', 'Student', 'Self-Employed'];
  const rows: string[] = [header];
  for (let i = 1; i <= 50; i++) {
    const st = states[(i - 1) % states.length];
    const cat = cats[(i - 1) % cats.length];
    const occ = occs[(i - 1) % occs.length];
    const gender = i % 3 === 0 ? 'Male' : 'Female';
    const age = occ === 'Student' ? 20 : 28 + ((i * 3) % 35);
    const income = 95000 + ((i * 15000) % 140000);
    const land = occ === 'Farmer' ? (1.0 + (i % 4) * 0.5).toFixed(1) : '0';
    const disability = i % 10 === 0 ? 'true' : 'false';
    const bpl = income <= 200000 ? 'true' : 'false';
    const res = i % 4 === 0 ? 'Urban' : 'Rural';
    rows.push(`FAM_${String(i).padStart(3, '0')},${age},${income},${st},${cat},${gender},${occ},${land},${disability},${bpl},${res}`);
  }
  return rows.join('\n');
}

export const FieldWorkerAndIvrView: React.FC<Props> = ({ profile }) => {
  // F4 Field-Worker Batch Screener
  const [csvInput, setCsvInput] = useState(() => generateDemo50FamiliesCsv());
  const [batchRes, setBatchRes] = useState<BatchResult | null>(null);
  const [batchLoading, setBatchLoading] = useState(false);

  // F5 Proactive Alerts
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [alertsChecked, setAlertsChecked] = useState(false);

  // P8 Voice + Missed-Call IVR Simulator
  const [ivrDigit, setIvrDigit] = useState('1');
  const [ivrTranscript, setIvrTranscript] = useState('నాకు రెండు ఎకరాల భూమి ఉంది తెలంగాణ రైతు భరోసా వస్తుందా');
  const [ivrRes, setIvrRes] = useState<IvrResponse | null>(null);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [voiceNotice, setVoiceNotice] = useState<string | null>(null);
  const voiceHandleRef = useRef<VoiceCaptureHandle | null>(null);

  useEffect(() => {
    return () => {
      voiceHandleRef.current?.stop();
      stopSpeaking();
    };
  }, []);

  const runBatch = async () => {
    setBatchLoading(true);
    try {
      const res = await fetch('/api/fieldworker/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ csvText: csvInput }),
      });
      if (res.ok) setBatchRes(await res.json());
    } finally {
      setBatchLoading(false);
    }
  };

  const downloadCsv = () => {
    if (!batchRes?.csv_output) return;
    const blob = new Blob([batchRes.csv_output], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'yojana_mitra_50_families_screened.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const runAlerts = async () => {
    const res = await fetch('/api/alerts/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label: `${profile.state} ${profile.category} Household`, profile }),
    });
    if (res.ok) {
      const data = await res.json();
      setAlerts(data.matched_alerts ?? []);
      setAlertsChecked(true);
    }
  };

  const runIvr = async (withTranscript: boolean) => {
    stopSpeaking();
    setSpeaking(false);
    const res = await fetch('/api/ivr/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        digit: ivrDigit,
        transcript: withTranscript ? ivrTranscript : '',
        profile,
      }),
    });
    if (res.ok) {
      const data = (await res.json()) as IvrResponse;
      setIvrRes(data);
    }
  };

  const toggleSpeakResponse = (text: string, langCode: string) => {
    if (speaking) {
      stopSpeaking();
      setSpeaking(false);
      return;
    }
    setVoiceNotice(null);
    speakText(text, langCode, {
      onStart: () => setSpeaking(true),
      onEnd: () => setSpeaking(false),
      onError: (msg) => {
        setVoiceNotice(msg);
        setSpeaking(false);
      },
    });
  };

  const toggleVoiceCapture = async () => {
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
    const digitToLang: Record<string, LanguageCode> = {
      '1': 'te',
      '2': 'hi',
      '3': 'en',
      '4': 'kn',
      '5': 'ta',
    };
    const activeLang: LanguageCode = digitToLang[ivrDigit] || 'te';
    const handle = await startVoiceInput({
      lang: activeLang,
      onInterim: (t) => setIvrTranscript(t),
      onFinal: (t) => setIvrTranscript(t),
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
          ? `Listening (${activeLang.toUpperCase()}) via free browser mic...`
          : 'Recording audio clip... tap Stop when finished.'
      );
    }
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h2 className="text-lg font-bold text-slate-900">
          Field-Worker Batch Mode, Proactive Alerts &amp; Voice IVR (F4, F5, P8)
        </h2>
        <p className="text-xs text-slate-500">
          Screen 50 rural families in one batch CSV, match daily scheme diff updates to saved profiles, and test the Exotel/Twilio missed-call IVR webhook.
        </p>
      </div>

      {/* F4: Field-Worker 50-Family Batch Screening */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Field-Worker Batch Screener (F4)</h3>
            <p className="text-xs text-slate-500">
              Upload or edit a CSV of up to 200 households. Target: &lt;2 min per family (deterministic engine screens 50 families in &lt;50 ms).
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => void runBatch()}
              disabled={batchLoading}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-700 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-800 whitespace-nowrap"
            >
              {batchLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Users className="h-3.5 w-3.5" />}
              Screen 50 Families Now
            </button>
            {batchRes && (
              <button
                type="button"
                onClick={downloadCsv}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 whitespace-nowrap"
              >
                <Download className="h-3.5 w-3.5" /> Export CSV
              </button>
            )}
          </div>
        </div>

        <textarea
          rows={4}
          value={csvInput}
          onChange={(e) => setCsvInput(e.target.value)}
          className="w-full rounded-lg border border-slate-300 bg-slate-50 p-3 font-mono-num text-[11px] text-slate-800"
        />

        {batchRes && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 border-t border-slate-200 pt-4">
              <div>
                <div className="text-xs text-slate-500">Families Screened</div>
                <div className="font-mono-num text-xl font-bold text-slate-900">{batchRes.families_screened}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Total Annual Welfare Unlocked</div>
                <div className="font-mono-num text-xl font-bold text-emerald-700">
                  ₹{batchRes.aggregate_annual_welfare_inr.toLocaleString('en-IN')}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Throughput Latency</div>
                <div className="font-mono-num text-xl font-bold text-slate-900">
                  {batchRes.avg_ms_per_family} ms / family
                </div>
              </div>
            </div>

            <div className="max-h-64 overflow-y-auto overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500">
                    <th className="py-2 pr-3 font-medium">Family ID</th>
                    <th className="py-2 pr-3 font-medium">State · Cat · Occ</th>
                    <th className="py-2 pr-3 font-medium">Optimal Stacked Schemes</th>
                    <th className="py-2 text-right font-medium">Annual ₹</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {batchRes.results.slice(0, 15).map((r) => (
                    <tr key={r.family_id} className="hover:bg-slate-50">
                      <td className="py-2 pr-3 font-mono-num font-medium text-slate-900">{r.family_id}</td>
                      <td className="py-2 pr-3 text-slate-600">
                        {r.state} · {r.category} · {r.occupation}
                      </td>
                      <td className="py-2 pr-3 text-slate-700 max-w-md truncate">{r.top_stacked_schemes || '—'}</td>
                      <td className="py-2 text-right font-mono-num font-semibold text-slate-900">
                        ₹{r.total_annual_inr.toLocaleString('en-IN')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Split: Missed-Call IVR + Proactive Diff Alerts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 items-start">
        {/* P8: Voice + Missed-Call IVR Simulator */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Missed-Call IVR &amp; Voice Copilot (P8)</h3>
            <p className="text-xs text-slate-500">
              Simulates Exotel/Twilio callback: missed call → DTMF language menu (1–5) → Indic ASR query → deterministic voice answer + SMS.
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {[
              { d: '1', label: 'Press 1 · Telugu' },
              { d: '2', label: 'Press 2 · Hindi' },
              { d: '3', label: 'Press 3 · English' },
              { d: '4', label: 'Press 4 · Kannada' },
              { d: '5', label: 'Press 5 · Tamil' },
            ].map((k) => (
              <button
                key={k.d}
                type="button"
                onClick={() => setIvrDigit(k.d)}
                className={`rounded-md border px-2.5 py-1.5 text-xs font-medium transition-colors ${
                  ivrDigit === k.d
                    ? 'border-blue-600 bg-blue-50 text-blue-800'
                    : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                {k.label}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={ivrTranscript}
              onChange={(e) => setIvrTranscript(e.target.value)}
              className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900"
            />
            <button
              type="button"
              onClick={() => void toggleVoiceCapture()}
              className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-semibold whitespace-nowrap ${
                listening
                  ? 'border-red-400 bg-red-50 text-red-700'
                  : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
              }`}
            >
              {listening ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
              {listening ? 'Stop Mic' : 'Speak'}
            </button>
          </div>
          {voiceNotice && (
            <p className="text-xs text-slate-600" role="status">
              {voiceNotice}
            </p>
          )}

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void runIvr(false)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              <PhoneCall className="h-3.5 w-3.5" /> Step 1: Language Menu
            </button>
            <button
              type="button"
              onClick={() => void runIvr(true)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3.5 py-2 text-xs font-semibold text-white hover:bg-slate-800"
            >
              Step 2: Voice Query → Answer
            </button>
          </div>

          {ivrRes && (
            <div className="border-t border-slate-200 pt-3 space-y-2.5 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-semibold text-slate-800">
                  Stage: {ivrRes.stage} · Lang: {ivrRes.lang.toUpperCase()}
                </span>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => toggleSpeakResponse(ivrRes.spoken_response || ivrRes.tts_prompt || '', ivrRes.lang)}
                    className="inline-flex items-center gap-1 text-blue-700 font-semibold hover:underline"
                  >
                    {speaking ? <Square className="h-3 w-3" /> : <Volume2 className="h-3.5 w-3.5" />}
                    {speaking ? 'Stop TTS' : 'Play TTS'}
                  </button>
                  <a
                    href={buildWhatsAppShareUrl(ivrRes.spoken_response || ivrRes.tts_prompt || '')}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-emerald-700 font-semibold hover:underline"
                  >
                    <MessageCircle className="h-3.5 w-3.5" /> Share on WhatsApp
                  </a>
                </div>
              </div>
              <p className="rounded-lg bg-slate-50 p-3 text-slate-800">
                {ivrRes.spoken_response || ivrRes.tts_prompt}
              </p>
              <div className="rounded-lg bg-slate-900 p-3 font-mono-num text-[11px] text-slate-100 overflow-x-auto">
                {ivrRes.twiml}
              </div>
            </div>
          )}
        </div>

        {/* F5: Proactive Diff-Log Alerts (WhatsApp / Telegram Preview) */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
          <div className="flex items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Proactive Diff-Log Alerts (F5)</h3>
              <p className="text-xs text-slate-500">
                Matches daily added/changed schemes from <code className="font-mono-num">diff_log.json</code> against saved citizen profiles for instant WhatsApp share.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void runAlerts()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-700 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-800 whitespace-nowrap shrink-0"
            >
              <Bell className="h-3.5 w-3.5" /> Match Diff Log
            </button>
          </div>

          {!alertsChecked ? (
            <p className="text-xs text-slate-500">
              Click &ldquo;Match Diff Log&rdquo; to evaluate recent policy changes against the active citizen profile ({profile.state} · {profile.category} · {profile.occupation}).
            </p>
          ) : alerts.length === 0 ? (
            <p className="text-xs text-slate-500">
              No newly added or updated schemes in the latest diff snapshot match this profile. Switch to the Telangana SC Woman Farmer profile to see the Rythu Bharosa benefit update alert.
            </p>
          ) : (
            <div className="space-y-3">
              {alerts.map((a) => (
                <div key={a.scheme_id} className="rounded-lg border border-emerald-200 bg-emerald-50/60 p-3.5 space-y-2 text-xs">
                  <div className="flex items-center justify-between font-semibold text-emerald-900">
                    <span>WhatsApp Alert · {a.scheme_name}</span>
                    <span className="font-mono-num">₹{a.annual_benefit_inr.toLocaleString('en-IN')}/yr</span>
                  </div>
                  <p className="text-slate-700 leading-relaxed">{a.whatsapp_preview}</p>
                  <div className="pt-1">
                    <a
                      href={buildWhatsAppShareUrl(a.whatsapp_preview)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-md bg-emerald-700 px-2.5 py-1 text-xs font-semibold text-white hover:bg-emerald-800 transition-colors"
                    >
                      <MessageCircle className="h-3.5 w-3.5" /> Send via WhatsApp
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
