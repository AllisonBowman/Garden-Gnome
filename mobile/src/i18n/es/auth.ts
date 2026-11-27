// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/auth';

const auth: Strings<typeof en> = {
  signInReason: 'Al iniciar sesión se crea tu cuenta, así tus plantas, tu registro de cuidados y tus áreas de cultivo te siguen a un teléfono nuevo.',
  tagline: 'Cuida tu terreno y tus plantas a lo largo de las temporadas.',
  signInWithGoogle: 'Iniciar sesión con Google',
  webNote: 'Para iniciar sesión necesitas la app de PlantAdvocate: el inicio de sesión con Apple y Google no está disponible en la vista previa del navegador.',
  failed: 'No se completó el inicio de sesión. Intenta de nuevo.',
  footer: 'Tus plantas siguen siendo tuyas: son privadas de forma predeterminada, y el censo anónimo es estrictamente opcional.',
};

export default auth;
