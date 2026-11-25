import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  FileScan,
  Loader2,
  ShieldCheck,
  Upload,
} from 'lucide-react';
import type { CitizenProfile, RejectionPrediction, ScamAnalysis } from '../lib/types';

interface Props {
  profile: CitizenProfile;
  onApplyExtractedProfile: (partial: Partial<CitizenProfile>) => void;
  consentGiven: boolean;
  onGiveConsent: () => void;
  rejectionRisks: RejectionPrediction[];
  onRefreshRejection: (opts: { aadhaarSeeded: boolean; certAgeMonths: number }) => Promise<void>;
}

const SCAM_SAMPLES = [
  {
    label: 'Fake PM-KISAN KYC Scam',
    text: 'URGENT: Your PM-KISAN Rs 6000 installment is BLOCKED! Update Aadhaar & OTP at https://pmkisan-kyc-update.top within 2 hours and pay Rs 499 registration fee via UPI.',
  },
  {
    label: 'WhatsApp Free Laptop Hoax',
    text: 'CONGRATULATIONS! PM Free Laptop & Rs 50,000 Yojana approved! Forward to 10 WhatsApp groups and download RythuBharosa_Update.apk from http://pm-free-cash-2026.xyz.',
  },
  {
    label: 'Legitimate Official Notice',
    text: 'Official Notice: Verify your PM-KISAN e-KYC and beneficiary status only on https://pmkisan.gov.in or at your nearest CSC center. No registration fee is charged. Never share your OTP.',
  },
];

const SAMPLE_DOC_TEXT = `Government of Telangana - MeeSeva Integrated Income & Caste Certificate
Applicant Name: Lakshmi Devi, W/o Venkatesh
Aadhaar Number: 2345 6789 0123 | Mobile: +91 9876543210 | PAN: ABCDE1234F
State: Telangana | District: Warangal Rural Mandal, Village Narsampet
Age: 38 | Gender: Female | Category: Scheduled Caste (SC)
Annual Family Income: Rs 1,40,000
Pattadar Passbook (Dharani) Extent: 2.0 acres | Occupation: Farmer
Telangana White Ration Card / Food Security Card Holder`;

export const ScamAndDocView: React.FC<Props> = ({
  profile,
  onApplyExtractedProfile,
  consentGiven,
  onGiveConsent,
  rejectionRisks,
  onRefreshRejection,
}) => {
  // Scam Shield state
  const [scamInput, setScamInput] = useState(SCAM_SAMPLES[0].text);
  const [scamRes, setScamRes] = useState<(ScamAnalysis & { masked_message?: string }) | null>(null);
  const [scamLoading, setScamLoading] = useState(false);

  // Document OCR state
  const [docText, setDocText] = useState(SAMPLE_DOC_TEXT);
  const [ocrRes, setOcrRes] = useState<{
    extracted_profile: Partial<CitizenProfile>;
    masked_ocr_preview: string;
    pii_redacted_types: string[];
    raw_document_deleted: boolean;
    aadhaar_stored: boolean;
    vision_used?: boolean;
  } | null>(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrError, setOcrError] = useState('');

  // Rejection Risk controls
  const [aadhaarSeeded, setAadhaarSeeded] = useState(true);
  const [certAge, setCertAge] = useState(6);

  const checkScam = async () => {
    if (!scamInput.trim()) return;
    setScamLoading(true);
    try {
      const res = await fetch('/api/scam/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: scamInput }),
      });
      if (res.ok) setScamRes(await res.json());
    } finally {
      setScamLoading(false);
    }
  };

  const runOcr = async (imageBase64?: string, mimeType?: string) => {
    setOcrError('');
    setOcrLoading(true);
    try {
      const res = await fetch('/api/ocr/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(imageBase64 ? { imageBase64, mimeType } : { text: docText }),
      });
      const data = await res.json();
      if (!res.ok) {
        setOcrError(data.error || 'Document scan failed.');
      } else {
        setOcrRes(data);
      }
    } finally {
      setOcrLoading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const resultStr = String(reader.result || '');
      const base64 = resultStr.includes(',') ? resultStr.split(',')[1] : resultStr;
      void runOcr(base64, file.type || 'image/jpeg');
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h2 className="text-lg font-bold text-slate-900">Scam Shield, Document Scan &amp; Rejection Risk (F3, F6, F7)</h2>
        <p className="text-xs text-slate-500">
          Verify forwarded WhatsApp/SMS welfare claims, extract profile fields with zero-Aadhaar DPDP redaction, and inspect rejection predictors.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 items-start">
        {/* F6: Scam Shield */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Welfare Scam Detector (F6)</h3>
            <p className="text-xs text-slate-500">
              Paste any forwarded SMS or WhatsApp message to check for phishing domains, fake UPI fees, APK lures, and verify the real .gov.in portal.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {SCAM_SAMPLES.map((s) => (
              <button
                key={s.label}
                type="button"
                onClick={() => setScamInput(s.text)}
                className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-blue-50 hover:text-blue-800"
              >
                {s.label}
              </button>
            ))}
          </div>

          <textarea
            rows={4}
            value={scamInput}
            onChange={(e) => setScamInput(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white p-3 text-xs text-slate-900 focus:border-blue-600 focus:outline-none"
          />

          <button
            type="button"
            onClick={() => void checkScam()}
            disabled={scamLoading}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800"
          >
            {scamLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5" />}
            Analyze Message
          </button>

          {scamRes && (
            <div className="border-t border-slate-200 pt-4 space-y-3">
              <div className="flex items-center justify-between">
                <span
                  className={`inline-flex items-center gap-1.5 text-sm font-bold ${
                    scamRes.verdict === 'SCAM' ? 'text-red-700' : 'text-emerald-700'
                  }`}
                >
                  {scamRes.verdict === 'SCAM' ? (
                    <AlertTriangle className="h-4 w-4" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4" />
                  )}
                  Verdict: {scamRes.verdict}
                </span>
                <span className="font-mono-num text-xs text-slate-600">
                  Risk {Math.round(scamRes.risk_score * 100)}% · Confidence {Math.round(scamRes.confidence * 100)}%
                </span>
              </div>

              {scamRes.red_flags.length > 0 && (
                <ul className="space-y-1.5 text-xs text-red-800">
                  {scamRes.red_flags.map((flag, i) => (
                    <li key={i}>• {flag}</li>
                  ))}
                </ul>
              )}

              {scamRes.llm_explanation && (
                <p className="rounded-lg bg-slate-50 p-3 text-xs text-slate-700 leading-relaxed">
                  {scamRes.llm_explanation}
                </p>
              )}

              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs">
                <span className="text-slate-700">
                  Verified Official Portal: <strong>{scamRes.official_scheme}</strong>
                </span>
                <a
                  href={scamRes.official_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 font-semibold text-blue-700 hover:underline whitespace-nowrap"
                >
                  {scamRes.official_url.replace('https://', '')} <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          )}
        </div>

        {/* F3: Document Scan & DPDP PII-Masked Autofill */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Document Scan &amp; Profile Autofill (F3)</h3>
            <p className="text-xs text-slate-500">
              Extracts structured profile fields from Income/Caste/Pattadar certificates. Aadhaar, phone, PAN, and names are masked immediately and uploaded documents are deleted after extraction (DPDP Act 2023).
            </p>
          </div>

          {!consentGiven ? (
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 space-y-3 text-xs text-blue-900">
              <div className="font-semibold">DPDP Act 2023 Informed Consent Required</div>
              <p>
                Before scanning a document, confirm that you consent to ephemeral in-memory field extraction. Raw files and Aadhaar numbers are never written to disk or databases.
              </p>
              <button
                type="button"
                onClick={onGiveConsent}
                className="rounded-lg bg-blue-700 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-800"
              >
                I Consent (DPDP Act 2023)
              </button>
            </div>
          ) : (
            <>
              <textarea
                rows={5}
                value={docText}
                onChange={(e) => setDocText(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white p-3 font-mono-num text-[11px] text-slate-800 focus:border-blue-600 focus:outline-none"
              />

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => void runOcr()}
                  disabled={ocrLoading}
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-700 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-800"
                >
                  {ocrLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileScan className="h-3.5 w-3.5" />}
                  Extract &amp; Mask PII
                </button>

                <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50">
                  <Upload className="h-3.5 w-3.5" />
                  Upload Certificate Image
                  <input type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />
                </label>
              </div>

              {ocrError && <p className="text-xs text-red-700">{ocrError}</p>}

              {ocrRes && (
                <div className="border-t border-slate-200 pt-4 space-y-3 text-xs">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-emerald-800">
                    <span className="font-semibold">
                      Redacted PII: {ocrRes.pii_redacted_types.join(', ') || 'None'} · Aadhaar Stored: NO · Raw Doc Deleted: YES
                    </span>
                    <button
                      type="button"
                      onClick={() => onApplyExtractedProfile(ocrRes.extracted_profile)}
                      className="rounded-md bg-emerald-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-800"
                    >
                      Autofill Citizen Profile
                    </button>
                  </div>

                  <div className="rounded-lg bg-slate-50 p-3 font-mono-num text-[11px] text-slate-700 whitespace-pre-line">
                    {ocrRes.masked_ocr_preview}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {Object.entries(ocrRes.extracted_profile).map(([k, v]) => (
                      <div key={k} className="flex justify-between border-b border-slate-100 py-1">
                        <span className="text-slate-500">{k}</span>
                        <span className="font-mono-num font-semibold text-slate-900">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* F7: Full Rejection Risk Predictor Table */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Application Rejection Predictor (F7)</h3>
            <p className="text-xs text-slate-500">
              Models rule-margin tightness, Aadhaar-NPCI DBT bank seeding, and certificate age for {profile.state} · {profile.category} · {profile.occupation}.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs">
            <label className="inline-flex items-center gap-2 text-slate-700">
              <input
                type="checkbox"
                checked={aadhaarSeeded}
                onChange={(e) => {
                  setAadhaarSeeded(e.target.checked);
                  void onRefreshRejection({ aadhaarSeeded: e.target.checked, certAgeMonths: certAge });
                }}
              />
              Aadhaar-Bank NPCI Seeded
            </label>
            <label className="inline-flex items-center gap-2 text-slate-700">
              Certificate Age (months)
              <input
                type="number"
                min={1}
                max={36}
                value={certAge}
                onChange={(e) => {
                  const v = Number(e.target.value);
                  setCertAge(v);
                  void onRefreshRejection({ aadhaarSeeded, certAgeMonths: v });
                }}
                className="w-16 rounded border border-slate-300 px-2 py-1 font-mono-num text-xs"
              />
            </label>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2 pr-4 font-medium">Scheme</th>
                <th className="py-2 pr-4 font-medium">Risk Band</th>
                <th className="py-2 pr-4 text-right font-medium">Rejection Prob.</th>
                <th className="py-2 font-medium">Primary Rejection Risk &amp; Preventive Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rejectionRisks.map((r) => (
                <tr key={r.scheme_id} className="hover:bg-slate-50">
                  <td className="py-2.5 pr-4 font-semibold text-slate-900">{r.scheme_name}</td>
                  <td className="py-2.5 pr-4">
                    <span
                      className={`font-semibold ${
                        r.risk_band === 'HIGH'
                          ? 'text-red-700'
                          : r.risk_band === 'MEDIUM'
                            ? 'text-amber-700'
                            : 'text-emerald-700'
                      }`}
                    >
                      {r.risk_band}
                    </span>
                  </td>
                  <td className="py-2.5 pr-4 text-right font-mono-num text-slate-800">
                    {Math.round(r.rejection_probability * 100)}%
                  </td>
                  <td className="py-2.5 text-slate-600">
                    <div className="font-medium text-slate-800">{r.top_3_reasons[0]?.reason}</div>
                    <div className="text-[11px] text-slate-500">Fix: {r.top_3_reasons[0]?.mitigation}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
