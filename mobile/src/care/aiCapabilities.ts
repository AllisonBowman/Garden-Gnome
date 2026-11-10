// What the care engine can do right now, decided from GET /ai/status.
//
// The server exists for exactly this question (garden-gnome/app/routers/ai.py:
// "so the mobile app can gate its photo UI on reality instead of finding out
// via a stub answer"). Photo check-ups and free-text symptom reading are
// switched off in production today, and a button that answers "not switched
// on yet" is, to App Review and to a caretaker, a broken button. So the
// screens ask first and only offer what will work.
//
// Pure on purpose (no React Native imports) so jest can pin the rules.

/** The parts of GET /ai/status the app reads. The route also reports the
 *  plain advice engine, which the app has no reason to look at: rule-based
 *  advice is always available. */
export interface AiStatus {
  advisor_symptoms_backend: string;
  vision: {
    backend: string;
    model: string | null;
    /** True when a photo sent right now would reach a model. */
    ready: boolean;
    detail?: string;
  };
}

/** What the screens may offer, as one object. Every flag is false until the
 *  server says yes. */
export interface AiCapabilities {
  /** Show the photo check-up card. */
  photoDiagnosis: boolean;
  /** Show the free-text "anything wrong?" box above care advice. */
  symptoms: boolean;
}

/** One capability's name, for anything tied to it — a screen's card, or a
 *  privacy disclosure that only applies while the feature is offered. */
export type AiCapability = keyof AiCapabilities;

/** The capabilities before the server has answered, or when it can't: none. */
export const NO_CAPABILITIES: AiCapabilities = { photoDiagnosis: false, symptoms: false };

/** A photo check-up is offered only when the server says a photo would be
 *  examined. Unknown (not loaded, or the call failed) counts as no: the
 *  feature appears once the answer is yes, never the other way round. */
export function photoDiagnosisOffered(status: AiStatus | undefined): boolean {
  return status?.vision?.ready === true;
}

/** The free-text "anything wrong?" box is offered only when something other
 *  than the rule engine will read it. The rule engine's answer to a symptom
 *  is that it can't read symptoms, which is not an answer worth asking for. */
export function symptomsOffered(status: AiStatus | undefined): boolean {
  const backend = status?.advisor_symptoms_backend;
  return typeof backend === 'string' && backend !== '' && backend !== 'stub';
}
