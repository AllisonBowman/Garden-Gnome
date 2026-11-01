// The one-time question notice, driven without a phone: the alert and the
// keychain are stood in for, and the alert answers as the test tells it to.
const store = new Map<string, string>();
let answer: 'send' | 'not now' = 'send';
const asked: string[] = [];

jest.mock('react-native', () => ({
  Platform: { OS: 'ios' },
  Alert: {
    alert: (title: string, _body: string, buttons: { text: string; onPress: () => void }[]) => {
      asked.push(title);
      const pick = answer === 'send' ? buttons[1] : buttons[0];
      pick.onPress();
    },
  },
}));
jest.mock('expo-secure-store', () => ({
  getItemAsync: async (k: string) => store.get(k) ?? null,
  setItemAsync: async (k: string, v: string) => { store.set(k, v); },
}));

import { mayAskWith, questionToSend } from './questionUpload';
import { DATA_FLOWS, QUESTION_NOTICE } from './copy';

declare const require: (id: string) => any;
declare const __dirname: string;

beforeEach(() => {
  store.clear();
  asked.length = 0;
  answer = 'send';
});

test('a question exists only while the box is offered, and only with words in it', () => {
  expect(questionToSend(false, 'yellow leaves')).toBe('');
  expect(questionToSend(true, '   ')).toBe('');
  expect(questionToSend(true, '  yellow leaves ')).toBe('yellow leaves');
});

test('advice without a question goes ahead without asking', async () => {
  await expect(mayAskWith('')).resolves.toBe(true);
  expect(asked).toEqual([]);
});

test('the first question waits for a yes, and the yes is remembered', async () => {
  await expect(mayAskWith('yellow leaves')).resolves.toBe(true);
  expect(asked).toEqual([QUESTION_NOTICE.title]);
  await expect(mayAskWith('brown tips')).resolves.toBe(true);
  expect(asked).toHaveLength(1);
});

test('"Not now" sends nothing, and the notice comes back next time', async () => {
  answer = 'not now';
  await expect(mayAskWith('yellow leaves')).resolves.toBe(false);
  await expect(mayAskWith('yellow leaves')).resolves.toBe(false);
  expect(asked).toHaveLength(2);
});

test('the notice says where the question goes, what goes with it, and how to refuse', () => {
  expect(QUESTION_NOTICE.title).toMatch(/question/i);
  expect(QUESTION_NOTICE.body).toMatch(/outside AI service/);
  expect(QUESTION_NOTICE.body).toMatch(/nickname/);
  expect(QUESTION_NOTICE.body).toMatch(/care log/);
  expect(QUESTION_NOTICE.body).toMatch(/coordinates are not included/);
  expect(QUESTION_NOTICE.cancelLabel.length).toBeGreaterThan(0);
});

test('the Settings entry and the plant screen keep the promise to ask', () => {
  const advice = DATA_FLOWS.find((f) => f.id === 'advice')!;
  expect(advice.detail).toMatch(/asks before the first question is sent/);
  const screen: string = require('fs').readFileSync(
    require('path').join(__dirname, '../screens/PlantDetailScreen.tsx'), 'utf8');
  // The question reaches getAdvice only through the consent check.
  expect(screen).toMatch(/mayAskWith\(/);
  expect(screen).not.toMatch(/getAdvice\([^)]*\bsymptoms\b/);
});
