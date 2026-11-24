// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/weather';

const weather: Strings<typeof en> = {
  conditions: {
    Clear: 'Despejado',
    MostlyClear: 'Mayormente despejado',
    PartlyCloudy: 'Parcialmente nublado',
    MostlyCloudy: 'Mayormente nublado',
    Cloudy: 'Nublado',
    Rain: 'Lluvia',
    Drizzle: 'Llovizna',
    Showers: 'Chubascos',
    Thunderstorms: 'Tormentas eléctricas',
    Snow: 'Nieve',
    Windy: 'Con viento',
    Haze: 'Bruma',
    Foggy: 'Niebla',
  },
  exposure: {
    shelteredIndoor: 'Protegido y en interiores: el pronóstico casi no llega a tus plantas aquí. Toma el clima como contexto, no como una tarea.',
    partial: 'Parcialmente techado y al aire libre: las plantas aquí sienten la temperatura y algo de la lluvia.',
    open: 'Sin techo y al aire libre: las plantas aquí sienten todo el pronóstico.',
    indoorSome: 'Algo de clima llega a este lugar, pero la temperatura se mantiene estable como en interiores: piensa sobre todo en la lluvia y la luz, no en el frío.',
    roofed: 'Techado pero al aire libre: las plantas aquí sienten los cambios de temperatura, aunque casi no les llega la lluvia.',
  },
  lines: {
    daylight: '☀️ ~{{hours}} h de luz de día: la luz con la que cuentan ahora las plantas de exterior.',
    rainLikely: '🌧️ Probable lluvia ({{pct}}% el {{day}}): {{reach}}; revisa el suelo después, antes de volver a regar.',
    reachPartial: 'puede que parte llegue a las plantas de aquí',
    reachOpen: 'puede regar las plantas sin protección de aquí',
    hot: '🔥 Racha de calor (máxima de {{high}}°F el {{day}}): las plantas aquí se secan más rápido; revisa el suelo antes.',
    cold: '❄️ Noche fría (mínima de {{low}}°F el {{day}}): quizá convenga cubrir las plantas delicadas de aquí o meterlas.',
    uv: '😎 UV muy alto (hasta {{peak}}): incluso las plantas de sol pueden quemarse aquí al mediodía.',
  },
  credit: {
    fallback: 'Clima',
    a11y: '{{label}}. Abre la página de atribución del proveedor de datos del clima.',
  },
};

export default weather;
