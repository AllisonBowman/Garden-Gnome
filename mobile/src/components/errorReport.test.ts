import { buildProblemMailto, describeError } from './errorReport';

const decode = (mailto: string) => {
  const [address, query] = mailto.replace(/^mailto:/, '').split('?');
  const params = new Map(query.split('&').map((kv) => {
    const [k, v] = kv.split('=');
    return [k, decodeURIComponent(v)] as [string, string];
  }));
  return { address, subject: params.get('subject'), body: params.get('body') ?? '' };
};

const report = {
  supportEmail: 'support@plantadvocate.ai',
  appVersion: '1.1.3',
  platform: 'ios',
  where: 'Census',
  error: new TypeError('Cannot convert undefined or null to object'),
};

test('the report goes to support with a plain subject', () => {
  const mail = decode(buildProblemMailto(report));
  expect(mail.address).toBe('support@plantadvocate.ai');
  expect(mail.subject).toBe('Report a problem in PlantAdvocate');
});

test('the body carries where it happened, what was thrown and the version', () => {
  const { body } = decode(buildProblemMailto(report));
  expect(body).toContain('Where: Census');
  expect(body).toContain('TypeError: Cannot convert undefined or null to object');
  expect(body).toContain('App: PlantAdvocate 1.1.3 (ios)');
  // The person writes their part first.
  expect(body.indexOf('Tell us what you were doing')).toBe(0);
});

test('whatever was thrown becomes one short line', () => {
  expect(describeError(new Error('a\n  b'))).toBe('Error: a b');
  expect(describeError('plain string')).toBe('plain string');
  expect(describeError({ code: 7 })).toBe('{"code":7}');
  expect(describeError(undefined)).toBe('undefined');
  expect(describeError(new Error(''))).toBe('Error');
  const long = describeError(new Error('x'.repeat(1000)));
  expect(long.length).toBeLessThanOrEqual(301);
  expect(long.endsWith('…')).toBe(true);
});

test('a value that cannot be serialised still describes itself', () => {
  const circular: Record<string, unknown> = {};
  circular.self = circular;
  expect(describeError(circular)).toBe('[object Object]');
});
