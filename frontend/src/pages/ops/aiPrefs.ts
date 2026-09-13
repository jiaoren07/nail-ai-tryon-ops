/** Batch H: operator-tunable AI assistant prefs (O7「AI 助手偏好」).
 *
 * Stored per-browser in localStorage and sent with every /api/ops/chat
 * request, where the backend clamps and applies them. Deliberately NOT
 * server-side state: the public deployment resets its DB on every cold
 * start, so localStorage actually persists longer for a visitor. */

export interface AiPrefs {
  modelTier: "strong" | "quick";
  useFc: boolean;
  temperature: number;
}

export const DEFAULT_AI_PREFS: AiPrefs = {
  modelTier: "strong",
  useFc: true,
  temperature: 0.7,
};

const STORAGE_KEY = "ops_ai_prefs";

export function loadAiPrefs(): AiPrefs {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<AiPrefs>;
      return {
        modelTier: parsed.modelTier === "quick" ? "quick" : "strong",
        useFc: parsed.useFc !== false,
        temperature:
          typeof parsed.temperature === "number"
            ? Math.min(Math.max(parsed.temperature, 0), 1)
            : DEFAULT_AI_PREFS.temperature,
      };
    }
  } catch {
    // corrupted / unavailable storage -> defaults
  }
  return { ...DEFAULT_AI_PREFS };
}

export function saveAiPrefs(prefs: AiPrefs): boolean {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    return true;
  } catch {
    return false;
  }
}

/** Request-body shape the backend expects (snake_case). */
export function toChatPrefs(prefs: AiPrefs) {
  return {
    model_tier: prefs.modelTier,
    use_fc: prefs.useFc,
    temperature: prefs.temperature,
  };
}
