// Whether Add plant offers "Take photo" / "Choose photo" to suggest a species.
//
// Off from 1.2.0 (build spec A10, "prune photo identification"). The native
// module and identify.ts stay in the app for now; only the way in is hidden.
// Turning this back on is the whole change, and entry.test.ts pins that the
// screen still reads it.
export const PHOTO_ID_ENTRY_SHOWN: boolean = false;
