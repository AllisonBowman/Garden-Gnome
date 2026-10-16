import React, { useMemo } from 'react';
import { Platform, StyleSheet, View } from 'react-native';
import { Button, Text } from 'react-native-paper';
import { useAppTheme } from '../theme/ThemeProvider';
import { ALMANAC, Palette } from '../theme/tokens';
import { APP_VERSION, SUPPORT_EMAIL, openExternal } from '../support';
import { buildProblemMailto } from './errorReport';

interface Props {
  /** Which part of the app this guards, for the report email. */
  where: string;
  /** Runs before the guarded screen is shown again, e.g. to drop cached
   *  server data that may be what broke it and fetch it fresh. */
  onReset?: () => void;
  children: React.ReactNode;
}

interface State {
  error: unknown;
  failed: boolean;
}

/**
 * Catches a render error in one part of the app and shows a card in its
 * place, instead of letting it take the whole app down.
 *
 * On iOS a render error nothing catches is fatal in a release build: one
 * unexpected null from the server used to end the session (the 1.1.2
 * Species tab, the Census tab against today's production API). Behind this
 * it costs one screen. The rest of the app, the tab bar and the header's
 * back button keep working, "Try again" fetches the data again and redraws
 * the screen, and "Report this problem" opens a support email with the
 * detail in it.
 */
export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null, failed: false };

  static getDerivedStateFromError(error: unknown): State {
    return { error, failed: true };
  }

  componentDidCatch(error: unknown, info: React.ErrorInfo): void {
    if (typeof __DEV__ !== 'undefined' && __DEV__) {
      console.error(`Caught in ${this.props.where}:`, error, info.componentStack);
    }
  }

  private retry = () => {
    try {
      this.props.onReset?.();
    } catch {
      // A failed refresh is no reason to stay stuck: the screen fetches on
      // its own when it mounts again. Rethrowing from a button handler would
      // be the very crash this exists to prevent.
    }
    this.setState({ error: null, failed: false });
  };

  render() {
    if (this.state.failed) {
      return <ErrorCard where={this.props.where} error={this.state.error} onRetry={this.retry} />;
    }
    return this.props.children;
  }
}

/**
 * Wrap a navigator screen so a crash costs that screen only. Called once at
 * module level per screen, never inside a render, so the wrapper keeps its
 * identity and the screen is not remounted on every render.
 */
export function guarded<P extends object>(
  Screen: React.ComponentType<P>,
  where: string,
  onReset?: () => void,
): React.ComponentType<P> {
  function Guarded(props: P) {
    return (
      <ErrorBoundary where={where} onReset={onReset}>
        <Screen {...props} />
      </ErrorBoundary>
    );
  }
  Guarded.displayName = `Guarded(${where})`;
  return Guarded;
}

/** The theme's palette, or the default one if the theme itself is what
 *  failed: the card that reports a crash must not crash. */
function usePaletteOrDefault(): Palette {
  try {
    return useAppTheme().palette;
  } catch {
    return ALMANAC;
  }
}

function ErrorCard({ where, error, onRetry }: { where: string; error: unknown; onRetry: () => void }) {
  const palette = usePaletteOrDefault();
  const styles = useMemo(() => makeStyles(palette), [palette]);
  const report = () => openExternal(buildProblemMailto({
    supportEmail: SUPPORT_EMAIL,
    appVersion: APP_VERSION,
    platform: Platform.OS,
    where,
    error,
  }));

  return (
    <View style={styles.screen}>
      <View style={styles.card}>
        <Text style={styles.title}>Something went wrong here</Text>
        <Text style={styles.body}>
          This screen ran into a problem. Nothing you’ve saved is lost.
        </Text>
        <Button
          mode="contained"
          onPress={onRetry}
          style={styles.button}
          buttonColor={palette.acc}
          textColor={palette.btnInk}
        >
          Try again
        </Button>
        <Button
          mode="text"
          icon="flag-outline"
          onPress={report}
          textColor={palette.sub}
          style={styles.button}
        >
          Report this problem
        </Button>
      </View>
    </View>
  );
}

const makeStyles = (p: Palette) => StyleSheet.create({
  screen: {
    flex: 1, justifyContent: 'center', alignItems: 'center',
    padding: 24, backgroundColor: p.bg,
  },
  card: {
    width: '100%', maxWidth: 360, padding: 20, borderRadius: 14,
    backgroundColor: p.card, borderWidth: StyleSheet.hairlineWidth, borderColor: p.line2,
  },
  title: { fontSize: 18, fontWeight: '700', color: p.ink, marginBottom: 8 },
  body: { fontSize: 14.5, lineHeight: 21, color: p.sub },
  button: { marginTop: 12, borderRadius: 8 },
});
