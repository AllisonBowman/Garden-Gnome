// English strings: notifications. The source of truth; es/notifications.ts mirrors its keys.
// Local reminders the app schedules itself (seasonal alert bodies come from the server).
const notifications = {
  careVerbs: {
    water: 'check',
    fertilize: 'feeding check',
    prune: 'pruning check',
    repot: 'root check',
    rotate: 'turning check',
  },
  windowWords: {
    fertilize: 'feeding',
    prune: 'pruning',
    rotate: 'turning',
  },
  repotTitle: '🪴 {{name}}\'s spring check-up',
  repotBody: 'Have a look at {{name}}: roots pushing out of the pot? Crown or roots showing at the surface? Wilting again soon after you water, or growth stalled? Repot if so — or just top-dress with fresh mix.',
  lookTitle: '🪴 {{name}} could use a look',
  waterBody: 'Check {{name}} — {{been}}. {{check}}',
  been_one: 'it\'s been {{count}} day',
  been_other: 'it\'s been {{count}} days',
  windowTitle: '🪴 Time to look at {{name}}',
  windowBody: '{{name}} has reached its {{window}} window. Have a look and decide whether it needs it.',
  lookBody: '{{name}} could use a look. Decide whether it needs anything.',
  batchTitle_one: '🪴 {{count}} plant could use a look today',
  batchTitle_other: '🪴 {{count}} plants could use a look today',
  batchItem: '{{name}} — {{verb}}',
  more: ' +{{count}} more',
  waterCheck: {
    moist: 'Its sources say {{regime}}; water if the surface feels dry.',
    depth: 'Feel the soil {{depth}} down; water only if it\'s dry there.',
    regime: 'Its sources say {{regime}}; feel the soil before you water.',
    plain: 'Feel the soil before you water.',
  },
  channel: 'Care reminders',
};

export default notifications;
