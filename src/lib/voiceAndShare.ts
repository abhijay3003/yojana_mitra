import { maskPii } from './piiMasker';
import type {
  CitizenProfile,
  CopilotQueryResponse,
  LanguageCode,
  RuleEvaluation,
  StackOptimizationResult,
} from './types';

export const PORTAL_DISCLAIMER = 'Informational only. Verify on the official portal.';

export const LANG_LOCALE_MAP: Record<LanguageCode, string> = {
  en: 'en-IN',
  te: 'te-IN',
  hi: 'hi-IN',
  kn: 'kn-IN',
  ta: 'ta-IN',
};

export interface BrowserSpeechRecognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onresult: ((event: {
    resultIndex?: number;
    results: ArrayLike<{
      isFinal?: boolean;
      0: { transcript: string };
    }>;
  }) => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

type SpeechRecognitionCtor = new () => BrowserSpeechRecognition;

export function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === 'undefined') return null;
  const win = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return win.SpeechRecognition || win.webkitSpeechRecognition || null;
}

export function isTtsSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
}

function stripMarkdownForSpeech(text: string): string {
  return text
    .replace(/https?:\/\/\S+/g, '')
    .replace(/[*_`#>~]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function stopSpeaking(): void {
  if (isTtsSupported()) {
    window.speechSynthesis.cancel();
  }
}

export function speakText(
  text: string,
  lang: LanguageCode | string,
  callbacks?: { onStart?: () => void; onEnd?: () => void; onError?: (msg: string) => void }
): boolean {
  if (!isTtsSupported()) {
    callbacks?.onError?.('Browser text-to-speech is not supported on this device.');
    return false;
  }
  const clean = stripMarkdownForSpeech(text);
  if (!clean) {
    callbacks?.onEnd?.();
    return false;
  }

  window.speechSynthesis.cancel();
  const locale = LANG_LOCALE_MAP[(lang as LanguageCode) || 'en'] || 'en-IN';
  const utter = new SpeechSynthesisUtterance(clean);
  utter.lang = locale;
  utter.rate = 0.96;

  // Prefer a matching regional Indic or Indian-English voice if installed on the OS/browser
  const voices = window.speechSynthesis.getVoices();
  const exactVoice = voices.find((v) => v.lang.toLowerCase() === locale.toLowerCase());
  const prefixVoice = voices.find((v) =>
    v.lang.toLowerCase().startsWith(locale.split('-')[0].toLowerCase())
  );
  const indianFallback = voices.find((v) => v.lang.toLowerCase().endsWith('-in'));
  if (exactVoice) {
    utter.voice = exactVoice;
  } else if (prefixVoice) {
    utter.voice = prefixVoice;
  } else if (indianFallback && locale === 'en-IN') {
    utter.voice = indianFallback;
  }

  utter.onstart = () => callbacks?.onStart?.();
  utter.onend = () => callbacks?.onEnd?.();
  utter.onerror = () => callbacks?.onEnd?.();

  window.speechSynthesis.speak(utter);
  return true;
}

/**
 * Starts browser-native Web Speech recognition (100% free, zero API keys).
 * Falls back to MediaRecorder + server-side Gemini audio transcription if
 * the browser does not implement SpeechRecognition (e.g., Firefox).
 */
export interface VoiceCaptureHandle {
  stop: () => void;
  mode: 'browser_speech' | 'media_recorder';
}

export async function startVoiceInput(options: {
  lang: LanguageCode;
  onInterim?: (text: string) => void;
  onFinal: (text: string) => void;
  onEnd: () => void;
  onError: (message: string) => void;
}): Promise<VoiceCaptureHandle | null> {
  const SpeechCtor = getSpeechRecognitionCtor();
  const locale = LANG_LOCALE_MAP[options.lang] || 'en-IN';

  if (SpeechCtor) {
    try {
      const recognition = new SpeechCtor();
      recognition.lang = locale;
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      let latestTranscript = '';

      recognition.onresult = (event) => {
        let combined = '';
        let hasFinal = false;
        for (let i = 0; i < event.results.length; i++) {
          const res = event.results[i];
          combined += res[0]?.transcript ?? '';
          if (res.isFinal) hasFinal = true;
        }
        latestTranscript = combined.trim();
        if (latestTranscript) {
          options.onInterim?.(latestTranscript);
          if (hasFinal) {
            options.onFinal(latestTranscript);
          }
        }
      };

      recognition.onerror = (ev) => {
        const code = ev.error || 'unknown';
        if (code === 'not-allowed' || code === 'service-not-allowed') {
          options.onError('Microphone access was blocked. Allow microphone permission in browser settings.');
        } else if (code === 'no-speech') {
          options.onError('No speech detected. Tap Speak and try again.');
        } else if (code !== 'aborted') {
          options.onError(`Voice capture error (${code}). You can type or retry.`);
        }
        options.onEnd();
      };

      recognition.onend = () => {
        if (latestTranscript) {
          options.onFinal(latestTranscript);
        }
        options.onEnd();
      };

      recognition.start();
      return {
        mode: 'browser_speech',
        stop: () => {
          try {
            recognition.stop();
          } catch {
            // ignore already stopped
          }
        },
      };
    } catch {
      // Fall through to MediaRecorder fallback
    }
  }

  // Fallback: MediaRecorder -> /api/voice/transcribe (server-side Gemini audio)
  if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
    options.onError('Voice input is not supported in this browser. Try Chrome, Edge, or Safari.');
    options.onEnd();
    return null;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4';

    const recorder = new MediaRecorder(stream, { mimeType });
    const chunks: BlobPart[] = [];

    recorder.ondataavailable = (ev) => {
      if (ev.data && ev.data.size > 0) chunks.push(ev.data);
    };

    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      try {
        const blob = new Blob(chunks, { type: mimeType.split(';')[0] });
        const base64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onloadend = () => {
            const raw = String(reader.result || '');
            resolve(raw.includes(',') ? raw.split(',')[1] : raw);
          };
          reader.onerror = () => reject(new Error('Audio read failed'));
          reader.readAsDataURL(blob);
        });

        const res = await fetch('/api/voice/transcribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            audioBase64: base64,
            mimeType: mimeType.split(';')[0],
            lang: options.lang,
          }),
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          options.onError(errData.error || 'Could not transcribe voice recording.');
        } else {
          const data = await res.json();
          if (data.transcript) {
            options.onFinal(String(data.transcript));
          } else {
            options.onError('No speech recognized from recording.');
          }
        }
      } catch {
        options.onError('Voice transcription request failed.');
      } finally {
        options.onEnd();
      }
    };

    recorder.start();
    // Safety auto-stop after 12 seconds so audio payload stays compact
    const timer = window.setTimeout(() => {
      if (recorder.state === 'recording') recorder.stop();
    }, 12000);

    return {
      mode: 'media_recorder',
      stop: () => {
        window.clearTimeout(timer);
        if (recorder.state === 'recording') {
          recorder.stop();
        }
      },
    };
  } catch {
    options.onError('Microphone permission denied or unavailable.');
    options.onEnd();
    return null;
  }
}

/**
 * Builds a DPDP-safe https://wa.me/?text=... deep link with PII redaction
 * and mandatory official-portal disclaimer. Zero Twilio / API keys required.
 */
export function buildWhatsAppShareUrl(rawText: string): string {
  const sanitized = maskPii(rawText).maskedText.trim();
  const withDisclaimer = sanitized.includes('Informational only.')
    ? sanitized
    : `${sanitized}\n\n${PORTAL_DISCLAIMER}`;
  return `https://wa.me/?text=${encodeURIComponent(withDisclaimer)}`;
}

export function formatSingleVerdictShareText(ev: RuleEvaluation): string {
  const lines = [
    `*Yojana Mitra — Verified Eligibility Check*`,
    `Scheme: ${ev.scheme_name} (${ev.state})`,
    `Verdict: ${ev.verdict.replace('_', ' ')} (Deterministic Rule Engine)`,
    `Est. Benefit: ₹${ev.annual_benefit_inr.toLocaleString('en-IN')}/year`,
  ];
  if (ev.failed.length > 0) {
    lines.push(`Failed clause: ${ev.failed[0].label}`);
  }
  lines.push(`Official Portal: ${ev.apply_url}`);
  lines.push(PORTAL_DISCLAIMER);
  return maskPii(lines.join('\n')).maskedText;
}

export function formatCopilotShareText(
  result: CopilotQueryResponse,
  selectedEval: RuleEvaluation | null
): string {
  const lines = [`*Yojana Mitra — Welfare Scheme Summary*`];
  if (selectedEval) {
    lines.push(`Top Scheme: ${selectedEval.scheme_name} (${selectedEval.state})`);
    lines.push(
      `Rule Verdict: ${selectedEval.verdict.replace('_', ' ')} · ₹${selectedEval.annual_benefit_inr.toLocaleString('en-IN')}/yr`
    );
    lines.push(`Official Portal: ${selectedEval.apply_url}`);
  }
  const compactAnswer = result.answer.replace(/\s+/g, ' ').trim().slice(0, 420);
  if (compactAnswer) {
    lines.push('', compactAnswer);
  }
  if (!compactAnswer.includes('Informational only.')) {
    lines.push('', PORTAL_DISCLAIMER);
  }
  return maskPii(lines.join('\n')).maskedText;
}

export function formatBenefitStackShareText(
  profile: CitizenProfile,
  stack: StackOptimizationResult,
  uniqueDocs: string[]
): string {
  const lines = [
    `*Yojana Mitra — Optimized Welfare Benefit Stack*`,
    `Profile: ${profile.state} · ${profile.category} · ${profile.occupation}`,
    `Total Est. Benefit: ₹${stack.total_annual_inr.toLocaleString('en-IN')}/year (${stack.selected_schemes.length} non-conflicting schemes, +${stack.gain_vs_top1_pct}% vs Top-1)`,
    '',
    `*Eligible Schemes:*`,
    ...stack.selected_schemes.map(
      (s, i) =>
        `${i + 1}. ${s.name} — ₹${s.annual_benefit_inr.toLocaleString('en-IN')}/yr\n   Portal: ${s.apply_url}`
    ),
  ];
  if (uniqueDocs.length > 0) {
    lines.push('', `*Documents Needed:* ${uniqueDocs.slice(0, 8).join(', ')}`);
  }
  lines.push('', PORTAL_DISCLAIMER);
  return maskPii(lines.join('\n')).maskedText;
}
