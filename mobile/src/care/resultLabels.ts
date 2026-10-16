// The small pill under an answer that says where its words came from. It
// names the kind of source a caretaker can weigh — the care rules, the care
// engine, the gnome's voice — and never the backend or the vendor behind it:
// the server reports those for operators, and a company's name on a badge is
// developer text that reached a user.

const RULE_ENGINE = 'stub';

/** Under care advice: "rule-based", or "care engine" for anything else the
 *  server reports, with "gnome voice" when the on-device restyle was kept. */
export function adviceSourceLabel(backend: string | null | undefined, gnomeStyled: boolean): string {
  const source = !backend || backend === RULE_ENGINE ? 'rule-based' : 'care engine';
  return gnomeStyled ? `${source} • gnome voice` : source;
}

/** Under a photo check-up's reading. The rule engine has no reading to give,
 *  so its answer is labelled as the feature not being on. */
export function diagnosisSourceLabel(backend: string | null | undefined): string {
  return !backend || backend === RULE_ENGINE ? 'not switched on yet' : 'photo check-up';
}
