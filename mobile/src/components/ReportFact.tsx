import React from 'react';
import { reportedFacts } from '../care/factReport';
import { Species } from '../types';
import ReportResult from './ReportResult';

/**
 * "Report a fact" on a species page: a prefilled support email naming the
 * species and carrying the page's facts as shown (care/factReport.ts), so a
 * reader who finds a wrong fact has a one-tap way to say so.
 */
export default function ReportFact({ species }: { species: Species }) {
  return (
    <ReportResult
      surfaceLabel="fact"
      result={reportedFacts(species)}
      context={[`Species: ${species.common_name} (${species.scientific_name})`]}
    />
  );
}
