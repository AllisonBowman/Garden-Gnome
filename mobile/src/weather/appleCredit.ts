import type { Forecast } from '../types/site';

/** Apple's attribution page, linked whenever Apple Weather supplied the forecast. */
export const APPLE_WEATHER_LEGAL = 'https://weatherkit.apple.com/legal-attribution.html';

/** Whether Apple Weather (WeatherKit) supplied this forecast. Its terms
 *  require the Apple Weather credit wherever its data, or advice restating
 *  it, is shown, so that credit stays on the face of a screen and never
 *  moves behind How we know. */
export function isAppleForecast(f: Pick<Forecast, 'provider' | 'provider_name'>): boolean {
  return /weatherkit|apple/i.test(`${f.provider} ${f.provider_name}`);
}
