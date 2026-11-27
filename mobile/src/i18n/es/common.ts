// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. The whole es/ folder
// is flagged by ES_META.needsReview in es/index.ts.
import type { Strings } from '../types';
import type en from '../en/common';

const common: Strings<typeof en> = {
  tryAgain: 'Intentar de nuevo',
  notNow: 'Ahora no',
  openSettings: 'Abrir Ajustes',
  cancel: 'Cancelar',
  ok: 'OK',
  errorCard: {
    title: 'Algo salió mal aquí',
    body: 'Esta pantalla tuvo un problema. No se perdió nada de lo que guardaste.',
    report: 'Reportar este problema',
  },
  cameraOff: {
    title: 'El acceso a la cámara está desactivado',
    body: 'PlantAdvocate no puede abrir la cámara porque el acceso a la cámara está desactivado. Puedes activarlo en Ajustes, o usar «Elegir foto» para escoger una imagen que ya tengas.',
  },
  locationOff: {
    title: 'El acceso a la ubicación está desactivado',
    body: 'PlantAdvocate no puede leer tu ubicación porque el acceso a la ubicación está desactivado. Puedes activarlo en Ajustes, o simplemente escribir la dirección.',
  },
  link: {
    title: 'No se pudo abrir el enlace',
    noMail: 'No hay ninguna app de correo configurada en este dispositivo. Puedes escribirnos a {{email}}.',
    cannotOpen: 'Tu dispositivo no pudo abrir {{url}}.',
  },
  report: {
    problemSubject: 'Reportar un problema en PlantAdvocate',
    problemPrompt: 'Cuéntanos qué estabas haciendo cuando pasó esto:',
    factPrompt: '¿Qué dato parece incorrecto y por qué? Un enlace a donde leíste otra cosa nos ayuda a verificarlo.',
    resultPrompt: 'Cuéntanos qué estuvo mal o fue inapropiado en este resultado:',
    factSubject: 'Reportar un dato',
    resultSubject: 'Reportar un resultado ({{surface}})',
  },
  photoId: {
    suggestions: 'Sugerencias a partir de la foto. Toca la que coincida y verifica que sea correcta antes de guardar.',
    suggested: 'Sugerencia a partir de la foto. Confirma que sea correcta o elige otra abajo.',
    unavailable: 'Tu teléfono no puede sugerir plantas a partir de fotos. Busca la tuya abajo.',
    unreadable: 'Esta vez no se pudo leer la foto. Busca tu planta abajo.',
    noName: 'Tu teléfono no pudo sugerir un nombre para esta. Búscala abajo.',
    notInCatalog: 'Tu teléfono sugirió «{{suggested}}», pero todavía no está en el catálogo. Busca abajo la opción más parecida.',
  },
};

export default common;
