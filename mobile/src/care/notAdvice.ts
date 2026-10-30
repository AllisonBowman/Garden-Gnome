// The line that goes under every hazard sentence.
//
// The App Store listing and the review notes promise it, and App Review
// reads a hazard note with no such line on screen as health advice
// (docs/go-to-market/research/review-risk.md). It is said word for word
// wherever it appears, so the app holds it once, here, and every screen
// shows it through components/NotAdviceNote.tsx. Change it only together
// with docs/app-store/listing.md and docs/app-store/review-notes.md.
//
// Pure on purpose (no React Native imports) so jest can pin it.
export const NOT_ADVICE_LINE =
  'These notes repeat what the sources publish. They are not medical or veterinary advice.';
