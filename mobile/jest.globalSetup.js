// Every test runs in one time zone, west of UTC, wherever it runs.
//
// The date bugs this app has had only show behind UTC: the server writes a
// day as 'YYYY-MM-DD', and `new Date('2026-07-08')` is midnight UTC, which is
// the evening before in New York. The CI runners sit on UTC, where that read
// happens to be right, so a test of it passed there whether the code was
// right or not. Set here, before any test file loads (and inherited by every
// worker), a date test means the same thing on a laptop and in CI.
module.exports = async () => {
  process.env.TZ = 'America/New_York';
};
