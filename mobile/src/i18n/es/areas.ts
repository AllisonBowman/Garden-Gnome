// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/areas';

const areas: Strings<typeof en> = {
  axis: {
    indoor_outdoor: 'Interior o exterior',
    sun: 'Sol',
    soil: 'Suelo',
    footprint: 'Tamaño',
    upkeep: 'Mantenimiento',
    goal: 'Para qué es',
  },
  listAnd: '{{head}} y {{last}}',
  confirmedHere: 'Confirmado aquí: {{list}}.',
  notKnownHere: 'Sin datos aquí: {{list}}.',
  misfitIntro: 'Conviene saberlo antes de plantarla en {{area}}',
  cantJudge: 'El catálogo todavía no puede evaluarla para {{area}}: no hay nada registrado '
    + 'a favor ni en contra allí, así que esto no es una recomendación en ningún sentido.',
  nothingAgainst: 'No hay nada registrado en su contra en {{area}}. Confirmado: {{list}}.',
  notKnown: 'Sin datos: {{list}}.',
  checkFailed: 'No se pudo consultar el catálogo en este momento; eso no significa que todo esté bien. '
    + 'Intenta de nuevo en un momento.',

  noAreaNote: 'Todavía no tienes áreas de cultivo, así que esta planta irá en una nueva llamada '
    + '“{{name}}”. Para que se revise el espacio con esta planta, primero '
    + 'agrega un espacio de cultivo desde Inicio.',
  areasFailedFrom: 'No se pudieron cargar tus áreas de cultivo en este momento, así que esta planta '
    + 'irá en el área de la que vienes. Después puedes moverla desde la página de la planta.',
  areasFailedOldest: 'No se pudieron cargar tus áreas de cultivo en este momento, así que esta planta '
    + 'irá en la más antigua. Después puedes moverla desde la página de la planta.',

  rankOrder: 'Cuanto más se haya confirmado aquí, más arriba aparece una especie; si empatan, van de la A a la Z.',
  listIntroOne: 'Una especie no tiene nada registrado en contra de este lugar y tiene al menos '
    + 'una cosa confirmada.',
  listIntroMany: '{{total}} especies no tienen nada registrado en contra de este lugar y tienen al menos '
    + 'una cosa confirmada. {{order}}',
  showingOf: 'Se muestran {{shown}} de {{total}}.',
  showingFirst: 'Se muestran las primeras {{shown}}.',
  cutTie: '{{showing}} La siguiente tiene tanto confirmado como la última de aquí, así que '
    + 'el punto donde se corta la lista depende del orden alfabético, no de la evidencia.',
  cutLess: '{{showing}} Todas las que siguen tienen menos confirmado.',

  surface: {
    in_ground_bed: '🌍 Cama en el suelo',
    raised_bed: '🪵 Cama elevada',
    containers: '🪴 Macetas',
    windowsill: '🪟 Alféizar',
    shelf_or_floor: '🗄️ Repisa o piso',
    hanging: '🌿 Colgante',
    greenhouse_bench: '🏕️ Mesa de invernadero',
    pond_or_water: '💧 Estanque o agua',
  },
  sunHint: 'Horas de sol directo al día: pleno sol es 6 o más, parcial de 3 a 6, sombra menos de 3.',
  indoorOutdoorHint: 'Exterior si sigue la temperatura de afuera, como un invernadero.',
  goal: {
    edible: { label: '🥕 Algo para comer', hint: 'Solo especies que se cultivan para comer.' },
    low_upkeep: { label: '😌 Poco mantenimiento', hint: 'Solo especies que aguantan que las dejes solas.' },
    pollinators: {
      label: '🐝 Alimenta a polinizadores',
      hint: 'Solo especies registradas como alimento de abejas, mariposas o colibríes.',
    },
  },
  areaType: {
    home: '🏠 Casa',
    nursery: '🌱 Vivero',
    community_garden: '🌳 Huerto comunitario',
    conservation: '🌿 Conservación',
    research: '🔬 Investigación',
    balcony: '🪴 Balcón',
    greenhouse: '🏕️ Invernadero',
    other: '📍 Otro',
  },
  needName: 'Ponle un nombre para continuar, uno con el que lo reconozcas entre tus otros espacios.',
  depthUnchecked: 'Se guarda con el espacio; todavía no se compara con ninguna planta.',
  dim: {
    areaLabel: 'Superficie (pies cuadrados)',
    areaHintBed: 'Más o menos cuánta cama hay por llenar.',
    areaHintWater: 'Superficie del agua.',
    areaHintOther: 'Cuánto espacio de repisa, alféizar o piso te da este lugar.',
    headroomLabel: 'Altura libre (pulgadas)',
    headroomHintBed: 'Qué tan alto puede crecer algo antes de dar sombra o amontonar a sus vecinas.',
    headroomHintOther: 'Distancia hasta la repisa, el mueble o el techo de arriba.',
    depthLabelBed: 'Profundidad del suelo (pulgadas)',
    depthLabelWater: 'Profundidad del agua (pulgadas)',
    depthLabelOther: 'Profundidad de la maceta (pulgadas)',
    depthHintBed: 'Hasta dónde pueden llegar las raíces antes de topar con suelo compactado, lona o roca.',
    depthHintWater: 'Profundidad en el escalón de siembra, no en el punto más hondo.',
    depthHintOther: 'Profundidad interior de las macetas que usarás aquí.',
  },
  twoSentences: '{{first}} {{second}}',
  measuredBoth: '{{said}} ({{inches}} pulg)',
  sqft: '{{n}} pies²',
  lengthEcho: 'Eso es {{said}}.',
  note: {
    indoorLight: 'La luz interior no se revisa: nada registra qué tan iluminado está este lugar, '
      + 'así que nada aquí se comparó por luz.',
    goalsUnanswered: 'Nada aquí está filtrado por lo que pediste ({{goals}}). '
      + 'Nada en esta lista tiene todavía una fuente que lo responda, así que la lista '
      + 'respeta el espacio, pero no tu deseo.',
    sizeUnchecked: 'El tamaño no se compara con tus medidas. Nada en esta lista tiene '
      + 'registrado un tamaño adulto para compararlo, así que no se sabe si algo '
      + 'llegaría a quedarle grande al espacio.',
    depthUnchecked: '{{depth}}: no se revisa; nada en esta lista se comparó con las '
      + '{{inches}} in que mediste.',
  },

  list: {
    plants_one: '{{count}} planta',
    plants_other: '{{count}} plantas',
    weather: 'Clima ›',
    loadFailed: 'No se pudieron cargar tus áreas de cultivo.',
    empty: 'Todavía no hay áreas de cultivo. Crea una para empezar.',
    newArea: 'Nueva área de cultivo',
  },
  setup: {
    stepTitles: {
      space: 'El espacio',
      conditions: 'Las condiciones',
      goals: 'Para qué es',
    },
    stepOf: 'Paso {{step}} de {{total}}',
    name: 'Nombre *',
    surfaceQ: '¿En qué van a estar las plantas?',
    roomQ: '¿Cuánto espacio hay?',
    roomHint: 'Deja en blanco lo que no hayas medido. En blanco significa desconocido, '
      + 'y nada se recomienda por suposición.',
    location: 'Ubicación',
    locationHint: 'Elige un lugar para ver el clima local. Busca una dirección o usa tu '
      + 'ubicación; solo se puede guardar un lugar real y confirmado.',
    presetFrom: 'Basado en “{{surface}}”. Cambia lo que no sea correcto.',
    conditionsHint: 'Describe cuánto del clima llega de verdad a este lugar.',
    shelter: 'Resguardo',
    sheltered: 'Resguardado',
    partial: 'Parcial',
    exposed: 'Expuesto',
    indoorOrOut: 'Interior o exterior',
    indoors: 'Interior',
    outdoors: 'Exterior',
    sun: 'Sol',
    fullSun: 'Pleno sol',
    shade: 'Sombra',
    kindOfPlace: 'Tipo de lugar',
    kindHint: 'Solo sirve para agrupar tus espacios en el censo; no '
      + 'cambia lo que se sugiere.',
    goalsHint: 'Elige las que apliquen, o ninguna. Reducen lo que se sugiere '
      + 'para este lugar; nunca lo amplían.',
    noGoals: 'Nada en particular: verás todo lo que se adapte al espacio.',
    cancel: 'Cancelar',
    back: 'Atrás',
    create: 'Crear',
    next: 'Siguiente',
    createFailedTitle: 'No se pudo crear',
    createFailedBody: 'Esta área de cultivo no se pudo guardar en este momento. Revisa tu conexión e '
      + 'intenta de nuevo; todo lo que escribiste sigue aquí.',
  },

  fit: {
    inArea: 'En {{area}}',
    tryAgain: 'Intentar de nuevo',
    against: 'En su contra aquí',
    confirmed: 'Confirmado aquí',
  },

  detail: {
    shelter: {
      sheltered: '🏠 Resguardado',
      partial: '⛱️ Cubierto en parte',
      exposed: '🌤️ Expuesto',
    },
    temp: {
      indoor: '🌡️ Interior',
      outdoor: '🍃 Exterior',
    },
    sun: {
      full_sun: '☀️ Pleno sol',
      partial_sun: '🌤️ Sol parcial',
      shade: '🌥️ Sombra',
    },
    thisArea: 'esta área de cultivo',
    saveFailedTitle: 'No se pudo guardar ese lugar',
    saveFailedBody: 'PlantAdvocate no pudo comunicarse con el servidor. Revisa tu conexión e intenta de nuevo.',
    addPlantHere: 'Agregar una planta aquí',
    theSpace: 'El espacio',
    unmeasured: 'Sin medir todavía: {{list}}. Mientras no se mida, nada se '
      + 'recomienda ni se descarta aquí por tamaño.',
    whatFor: 'Para qué es',
    noGoals: 'Nada en particular: cualquier cosa que se adapte al espacio.',
    needsAddressing: 'Requiere atención',
    tryAgain: 'Intentar de nuevo',
    noPlantsYet: 'Todavía no hay plantas aquí. Si este espacio tiene algo en contra de una planta '
      + 'que agregues aquí, aparecerá en esta tarjeta.',
    nothingContradicts: 'Nada aquí contradice el espacio. Las plantas que el catálogo no puede '
      + 'evaluar no aparecen como adecuadas; simplemente no aparecen.',
    goodCandidates: 'Buenas candidatas aquí',
    noCandidates: 'Todavía no hay nada que proponer. Una especie solo aparece aquí cuando una '
      + 'fuente confirma que le va bien a este lugar; una planta sin investigar '
      + 'no es una recomendación.',
    opensSpecies: 'Abre {{name}}, con qué tan bien le va a este espacio',
    seeAll: 'Ver las {{total}} en el Almanaque',
    seeRest: 'Ver el resto en el Almanaque',
    careCalendar: 'Calendario de cuidados',
    careFailed: 'No se pudo cargar el calendario de cuidados en este momento; eso no significa que todo esté bien.',
    noChecksNoPlants: 'Todavía no hay revisiones programadas aquí. Agrega plantas a esta área de cultivo y '
      + 'sus revisiones llenarán el calendario.',
    nothingInSeason: 'Por ahora no hay nada de temporada que revisar aquí.',
    localWeather: 'Clima local',
    noPlace: 'Esta área de cultivo todavía no tiene un lugar, así que no hay pronóstico que '
      + 'mostrar. Indica dónde está y el clima aparecerá.',
    savePlace: 'Guardar este lugar',
    noWeather: 'Todavía no hay clima disponible para este lugar.',
    humidity: '💧 {{pct}}% de humedad',
    outsideIn: 'AFUERA → AQUÍ DENTRO',
    perPlantTiming: 'El momento para cada planta está en los consejos de «Pregúntale al Gnomo» de cada una.',
  },
};

export default areas;
