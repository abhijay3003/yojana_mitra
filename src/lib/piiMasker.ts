/**
 * Yojana Mitra DPDP Act 2023 PII Masker (TypeScript mirror of /privacy/pii_masker.py).
 * Executes before every log line and before every Gemini API call.
 * Raw Aadhaar numbers are never stored or forwarded to external models.
 */

export const AADHAAR_TOKEN = '[REDACTED_AADHAAR]';
export const PHONE_TOKEN = '[REDACTED_PHONE]';
export const PAN_TOKEN = '[REDACTED_PAN]';
export const EMAIL_TOKEN = '[REDACTED_EMAIL]';
export const NAME_TOKEN = '[REDACTED_NAME]';

export interface MaskResult {
  maskedText: string;
  counts: Record<string, number>;
  redactedTypes: string[];
  hadPii: boolean;
}

const EMAIL_RE = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g;
const AADHAAR_SPACED_RE = /(?<!\d)[2-9]\d{3}[\s-]\d{4}[\s-]\d{4}(?!\d)/g;
const AADHAAR_COMPACT_RE = /(?<!\d)[2-9]\d{11}(?!\d)/g;
const AADHAAR_LABELED_RE = /(?:aadhaar|aadhar|uidai|uid|ఆధార్|आधार)\s*(?:no\.?|number|num|#|id|:|-|is)?\s*[:-]?\s*\d{4}[\s-]?\d{4}[\s-]?\d{4}/gi;
const PAN_RE = /\b[A-Z]{5}[0-9]{4}[A-Z]\b/g;
const PHONE_PREFIX_RE = /(?<!\d)(?:\+91[\s-]?|0091[\s-]?|91[\s-]|0)[6-9]\d{4}[\s-]?\d{5}(?!\d)/g;
const PHONE_PLAIN_RE = /(?<!\d)[6-9]\d{2}[\s-]?\d{3}[\s-]?\d{4}(?!\d)/g;
const NAME_EN_RE = /\b(my name is|i am|applicant name|beneficiary name|name\s*:|s\/o|d\/o|w\/o)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})/gi;
const NAME_TE_RE = /(నా పేరు|పేరు\s*:)\s*([\u0C00-\u0C7F]+(?:\s+[\u0C00-\u0C7F]+)?)/g;
const NAME_HI_RE = /(मेरा नाम|नाम\s*:)\s*([\u0900-\u097F]+(?:\s+[\u0900-\u097F]+)?)/g;

function replaceAndCount(input: string, regex: RegExp, replacement: string): [string, number] {
  let count = 0;
  const output = input.replace(regex, () => {
    count += 1;
    return replacement;
  });
  return [output, count];
}

export function maskPii(text: string): MaskResult {
  if (!text) {
    return { maskedText: '', counts: {}, redactedTypes: [], hadPii: false };
  }

  const counts: Record<string, number> = {
    aadhaar: 0,
    pan: 0,
    email: 0,
    phone: 0,
    name: 0,
  };

  let sanitized = text;
  let n = 0;

  [sanitized, n] = replaceAndCount(sanitized, EMAIL_RE, EMAIL_TOKEN);
  counts.email += n;

  [sanitized, n] = replaceAndCount(sanitized, AADHAAR_SPACED_RE, AADHAAR_TOKEN);
  counts.aadhaar += n;
  [sanitized, n] = replaceAndCount(sanitized, AADHAAR_COMPACT_RE, AADHAAR_TOKEN);
  counts.aadhaar += n;
  [sanitized, n] = replaceAndCount(sanitized, AADHAAR_LABELED_RE, AADHAAR_TOKEN);
  counts.aadhaar += n;

  [sanitized, n] = replaceAndCount(sanitized, PAN_RE, PAN_TOKEN);
  counts.pan += n;

  [sanitized, n] = replaceAndCount(sanitized, PHONE_PREFIX_RE, PHONE_TOKEN);
  counts.phone += n;
  [sanitized, n] = replaceAndCount(sanitized, PHONE_PLAIN_RE, PHONE_TOKEN);
  counts.phone += n;

  for (const pat of [NAME_EN_RE, NAME_TE_RE, NAME_HI_RE]) {
    sanitized = sanitized.replace(pat, (_m, prefix: string) => {
      counts.name += 1;
      return `${prefix} ${NAME_TOKEN}`;
    });
  }

  const activeCounts: Record<string, number> = {};
  const redactedTypes: string[] = [];
  for (const [k, v] of Object.entries(counts)) {
    if (v > 0) {
      activeCounts[k] = v;
      redactedTypes.push(k);
    }
  }

  return {
    maskedText: sanitized,
    counts: activeCounts,
    redactedTypes,
    hadPii: redactedTypes.length > 0,
  };
}
