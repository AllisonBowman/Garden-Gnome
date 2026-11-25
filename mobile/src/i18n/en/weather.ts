// English strings: weather. The source of truth; es/weather.ts mirrors its keys.
const weather = {
  /** WeatherKit condition codes. Codes not listed fall back to the code itself. */
  conditions: {
    Clear: 'Clear',
    MostlyClear: 'Mostly clear',
    PartlyCloudy: 'Partly cloudy',
    MostlyCloudy: 'Mostly cloudy',
    Cloudy: 'Cloudy',
    Rain: 'Rain',
    Drizzle: 'Drizzle',
    Showers: 'Showers',
    Thunderstorms: 'Thunderstorms',
    Snow: 'Snow',
    Windy: 'Windy',
    Haze: 'Haze',
    Foggy: 'Fog',
  },
  exposure: {
    shelteredIndoor: 'Sheltered and indoors — the forecast barely reaches your plants here. Treat weather as context, not a to-do.',
    partial: 'Partly covered and outdoors — plants here feel the temperature and some of the rain.',
    open: 'Open to the sky and outdoors — plants here feel the full forecast.',
    indoorSome: 'Some weather reaches this spot, but the temperature stays indoor-steady — mostly rain and light to think about, not cold.',
    roofed: 'Roofed but out in the open air — plants here feel the temperature swings, though rain mostly misses them.',
  },
  lines: {
    daylight: '☀️ ~{{hours}}h of daylight — the light budget outdoor plants get right now.',
    rainLikely: '🌧️ Rain likely ({{pct}}% {{day}}) — {{reach}}; check the soil afterwards before you water again.',
    reachPartial: 'some of it may reach plants here',
    reachOpen: 'it may water unsheltered plants here',
    hot: '🔥 Hot stretch (high {{high}} {{day}}) — plants here dry out faster; check soil sooner.',
    cold: '❄️ Cold night (low {{low}} {{day}}) — tender plants here may want cover or a move inside.',
    uv: '😎 Very high UV (up to {{peak}}) — even sun-lovers here can scorch at midday.',
  },
  credit: {
    fallback: 'Weather',
    a11y: '{{label}}. Opens the weather data provider\'s attribution page.',
  },
};

export default weather;
