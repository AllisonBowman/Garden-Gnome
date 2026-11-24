// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/capture';

const capture: Strings<typeof en> = {
  save: {
    nothingSaved: 'No se guardó nada',
    savedSome: 'Se guardaron {{saved}} de {{total}}',
    signedOut: 'Se cerró tu sesión, así que el resto no se guardó. Vuelve a iniciar sesión para agregarlas.',
    listStillHere: 'Tu lista sigue aquí.',
    othersStillHere_one: 'La otra {{count}} sigue aquí.',
    othersStillHere_other: 'Las otras {{count}} siguen aquí.',
    tryAgainSoon: 'Inténtalo de nuevo en un momento.',
    unreachable: 'PlantAdvocate no pudo conectarse con el servidor.',
    somethingWrong: 'Algo salió mal al guardarlas.',
    serverBusy: 'El servidor no pudo recibirlas en este momento.',
    refused: 'El servidor no las aceptó tal como están. Puede que una especie o un área de cultivo de la lista haya cambiado desde que empezaste.',
    checkList: 'Revisa la lista y vuelve a intentarlo.',
  },
  walk: {
    micNeeded: 'PlantAdvocate necesita el micrófono para escuchar. Todavía puedes escribir.',
    listeningOnDevice: 'Escuchando: di lo que está plantado. Nada sale de tu teléfono.',
    listeningApple: 'Escuchando: este dispositivo envía el audio a Apple para transcribirlo.',
    cantListen: 'No se pudo empezar a escuchar. Todavía puedes escribir.',
    nothingToAdd: 'No hay nada que agregar: intenta nombrar una planta.',
    eyebrow: 'CAMINA Y DI LO QUE VES',
    placeholder: 'Doce jitomates junto a la cerca sur, un romero junto a la puerta…',
    label: '¿Qué hay plantado aquí?',
    keyboardMic: 'Toca el micrófono de tu teclado para hablar en lugar de escribir.',
    listening: '● Escuchando: toca el cuadrado para detener.',
    catalogFailed: 'No se pudo cargar el catálogo de plantas, así que todavía no se puede reconocer nada de lo que digas. Lo que escribiste se queda aquí.',
    loadingCatalog: 'Cargando el catálogo…',
    addThese: 'Agregar estas',
    cameraOn: 'Activar la cámara',
    addAll: 'Agregar {{n}} al jardín',
    addSome: 'Agregar {{ready}} de {{total}}; elige una especie para el resto',
    howMany: 'Cuántas',
    cantPlace: 'No se pudo identificar esta; busca abajo.',
    pickOne: 'Elige la que quisiste decir.',
    searchCatalog: 'Buscar en el catálogo',
  },
};

export default capture;
