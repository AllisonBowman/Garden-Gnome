// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
// Consent copy: a reviewer should also check each sentence still says exactly
// what the English does, no more and no less.
import type { Strings } from '../types';
import type en from '../en/consent';

const consent: Strings<typeof en> = {
  destination: {
    device: 'Se queda en tu teléfono',
    server: 'Se envía a nuestro servidor',
    partner: 'Se comparte con otro servicio',
  },
  census: {
    fields:
      'su especie, cuántas hay, su etapa de crecimiento, el mes en que la conseguiste y '
      + 'cómo se veía entonces (suelo, hojas, plagas), cuántas veces se registró cada tipo de '
      + 'cuidado en cada mes, en cuántas áreas de cultivo ha estado y '
      + 'los meses en que pasó de una a otra, de qué planta se separó si fue así, '
      + 'y el tipo, la ciudad, la región y el país de su área de cultivo',
    leftOut:
      'No incluye nombre, correo electrónico, apodos, notas, fechas exactas ni '
      + 'coordenadas.',
    linking:
      'Cada planta y cada área de cultivo recibe una etiqueta nueva en cada exportación, y los '
      + 'registros se mezclan, así que ningún identificador une una exportación con otra. Eso '
      + 'es lo que prometemos, y nada más: los conteos mensuales de cuidados de una planta podrían '
      + 'parecerse de una exportación a la siguiente.',
  },
  flows: {
    identify: {
      title: 'Identificar una planta con una foto',
      summary: 'La foto se lee en tu teléfono y nunca se sube.',
      detail:
        'La propia IA de tu teléfono mira la imagen y sugiere un nombre — Apple '
        + 'Intelligence en iPhone, Gemini Nano en Android. La imagen no se nos envía '
        + 'a nosotros ni a nadie más. Si tu teléfono no puede hacerlo, '
        + 'la función simplemente lo dice en lugar de recurrir a subir la foto.',
    },
    diagnose: {
      title: 'Pedirle al Gnomo que revise una planta enferma',
      summary: 'Esta sí sube la foto. No se guarda.',
      detail:
        'Las revisiones con foto funcionan distinto de la identificación. La imagen, y '
        + 'cualquier nota que agregues, va a nuestro servidor, que la pasa a un servicio de IA '
        + 'externo para que la lea. La foto no se guarda en tu cuenta, y '
        + 'PlantAdvocate no la usa para entrenar nada. Solo la lectura, como '
        + 'texto, se guarda en la cronología de tu planta. La app pregunta antes de enviar '
        + 'la primera foto.',
    },
    care: {
      title: 'Tus plantas y tu registro de cuidados',
      summary: 'Apodos, especies y qué hiciste y cuándo.',
      detail:
        'Se guardan para que tu calendario sobreviva a un teléfono nuevo, y para que los consejos tomen '
        + 'en cuenta lo que de verdad has estado haciendo y no lo que dice la etiqueta. '
        + 'Es tu registro; puedes eliminar toda la cuenta, con todo '
        + 'lo que contiene, desde esta pantalla.',
    },
    advice: {
      title: 'Preguntas libres al Gnomo',
      summary: 'Tu pregunta va a un servicio de IA externo. Tus fotos no.',
      detail:
        'Los consejos de cuidado se basan en la base de datos de especies seleccionada. Cuando agregas una '
        + 'pregunta con tus propias palabras, nuestro servidor la envía a un servicio de IA '
        + 'externo para que la responda. Con ella van el apodo de la planta, los datos de su especie y su '
        + 'registro de cuidados reciente, y también el nombre, las condiciones y el pronóstico '
        + 'de su área de cultivo. Tu nombre, tu correo y tus coordenadas no se incluyen. La app '
        + 'pregunta antes de enviar la primera pregunta.',
    },
    voice: {
      title: 'Recorrer el jardín en voz alta',
      summary: 'Tu voz se convierte en texto en tu teléfono, o en Apple. Nunca recibimos el audio.',
      detail:
        'Recorre el jardín usa el micrófono solo mientras dice Escuchando. '
        + 'Se detiene cuando tocas detener o sales de la pantalla. Tu iPhone convierte la voz '
        + 'en texto en el propio teléfono cuando puede. Cuando no, iOS envía el '
        + 'audio al servicio de voz de Apple para transcribirlo, y la pantalla te dice '
        + 'cuál de los dos está pasando. PlantAdvocate nunca recibe el audio. Solo las '
        + 'plantas que confirmas — especie, cuántas y cualquier lugar que nombraste — llegan '
        + 'a tu cuenta, como texto.',
    },
    location: {
      title: 'La ubicación de un área de cultivo',
      summary: 'Las coordenadas van a servicios del tiempo. Nunca llegan al censo.',
      detail:
        'Cuando le das una dirección a un área de cultivo o usas tu ubicación actual, '
        + 'el propio servicio de mapas de tu teléfono la convierte en un lugar. Guardamos su ciudad, '
        + 'región, país y coordenadas. Para obtener el pronóstico de ese lugar, nuestro '
        + 'servidor consulta servicios del tiempo uno tras otro y se detiene en el primero que '
        + 'responde: Apple Weather, luego el Servicio Meteorológico Nacional de EE. UU. y luego '
        + 'Open-Meteo, que también cubre lugares fuera de EE. UU. Cada uno que se consulta '
        + 'recibe las coordenadas redondeadas a cerca de un kilómetro, y nada más '
        + 'sobre ti, y la tarjeta del pronóstico nombra al que respondió. '
        + 'Las coordenadas quedan fuera del censo comunitario por diseño, no '
        + 'por política.',
    },
    census: {
      title: 'El censo comunitario',
      summary: 'Desactivado a menos que lo actives.',
      detail:
        'El censo pregunta qué está cultivando toda la comunidad y cómo le está '
        + 'yendo, para que los consejos de cuidado mejoren para todos. Si te unes, se cuenta cada una de '
        + 'tus plantas: {{fields}}. {{leftOut}} '
        + '{{linking}} Si no te unes, no se cuenta ninguno de tus datos.',
    },
  },
  photoNotice: {
    title: 'Esto envía tu foto fuera de tu teléfono',
    body:
      'La revisión con foto es la única función que sube una imagen. Va a nuestro '
      + 'servidor con cualquier nota que agregues, y de ahí a un servicio de IA externo que la '
      + 'lee. La foto no se guarda, y PlantAdvocate no la usa para entrenar '
      + 'nada. Solo se conserva la lectura, en la cronología de tu planta.\n\n'
      + 'Identificar una planta es distinto: eso pasa por completo en tu teléfono.',
    confirm: 'Enviar la foto',
    cancel: 'Ahora no',
  },
  questionNotice: {
    title: 'Esto envía tu pregunta fuera de tu teléfono',
    body:
      'Una pregunta con tus propias palabras va a nuestro servidor y de ahí a un servicio de IA '
      + 'externo para que la responda. Con ella van el apodo de tu planta, los datos de su especie y su '
      + 'registro de cuidados reciente, y también el nombre, las condiciones y el pronóstico '
      + 'de su área de cultivo. Tu nombre, tu correo y tus coordenadas no se incluyen.\n\n'
      + '«Ahora no» no envía nada, y tu pregunta se queda en el cuadro.',
    confirm: 'Enviar mi pregunta',
    cancel: 'Ahora no',
  },
  censusConsent: {
    label: 'Unirme al censo comunitario',
    on: 'Se cuenta cada una de tus plantas: {{fields}}. {{leftOut}} {{linking}}',
    off:
      'Tus datos no se cuentan. Si activas esta opción, cada una de tus plantas se '
      + 'cuenta como lo describe «El censo comunitario» más abajo, sin nombre, correo, '
      + 'notas, fechas exactas ni coordenadas. Ayuda a que los consejos de cuidado mejoren '
      + 'para plantas como las tuyas; al desactivarla, deja de contar de inmediato. Los conteos '
      + 'ya tomados no se retiran.',
  },
  privacyIntro:
    'En pocas palabras: qué hace esta app con lo que le das. La política completa '
    + 'está enlazada al final y es la versión que vale.',
};

export default consent;
