import { isHazardSentence, toxicityLine } from './toxicityLine';

declare const require: (id: string) => any;
declare const __dirname: string;

// Sentences in the shapes the server writes them (app/services/toxicity.py
// describe), including the food-crop lead that puts the eaten part first.
const SEVERE_PEOPLE_ONLY =
  '⚠️ Seriously toxic to people. NC State rates its poison severity high. No toxicity '
  + 'to pets is recorded in our sources yet, which is not a guarantee of safety. If you '
  + 'suspect poisoning, call Poison Control (1-800-222-1222) right away.';
const MILD_PEOPLE_ONLY =
  'Mildly toxic to people. No verdict on pets is recorded yet, so treat it as unknown '
  + 'for them, not safe. Keep it out of reach of pets and children.';
const SEVERE_PETS = '⚠️ Seriously toxic to cats, dogs and people: leaves, stems (calcium '
  + 'oxalate). If you suspect poisoning, call Poison Control or a vet right away.';
const MILD_PETS = 'Toxic to cats: leaves. Keep it out of reach of pets and children.';
const FOOD_CROP = 'The tubers are the crop; the leaves, stems and sprouts are seriously '
  + 'toxic to people and pets. Keep trimmings out of reach of pets and children.';
const NOTHING_RECORDED = 'No toxicity is recorded for st. john’s wort in our sources yet. '
  + 'That is not a guarantee of safety — keep it away from pets that chew plants.';
const NO_VERDICT = 'No toxicity verdict recorded for fern yet — treat it as unknown rather '
  + 'than safe, and keep it away from pets that chew plants.';
const CITED_NONE = 'ASPCA records no toxicity to pets for spider plant. That is not a '
  + 'guarantee of safety — keep it away from pets that chew plants.';

test('a hazard to anyone reads as a hazard, whatever the pet flag says', () => {
  for (const s of [SEVERE_PEOPLE_ONLY, MILD_PEOPLE_ONLY, SEVERE_PETS, MILD_PETS, FOOD_CROP]) {
    expect(isHazardSentence(s)).toBe(true);
  }
});

test('"nothing on record" is a note, not a warning, and never "safe"', () => {
  for (const s of [NOTHING_RECORDED, NO_VERDICT, CITED_NONE]) {
    expect(isHazardSentence(s)).toBe(false);
    expect(toxicityLine({ toxicity_description: s, toxic_to_pets: null }))
      .toEqual({ text: s, hazard: false });
  }
});

test('a hazard to people alone gets the warning, though the pet flag is false', () => {
  // Poison Ivy, Bloodroot, Winter Daphne: severe for people, no pet flag.
  expect(toxicityLine({ toxicity_description: SEVERE_PEOPLE_ONLY, toxic_to_pets: false }))
    .toEqual({ text: SEVERE_PEOPLE_ONLY, hazard: true });
  expect(toxicityLine({ toxicity_description: MILD_PEOPLE_ONLY, toxic_to_pets: null }))
    .toEqual({ text: `⚠️ ${MILD_PEOPLE_ONLY}`, hazard: true });
});

test('every hazard carries exactly one warning sign', () => {
  const cases = [
    { toxicity_description: SEVERE_PETS, toxic_to_pets: true },
    { toxicity_description: MILD_PETS, toxic_to_pets: true },
    { toxicity_description: SEVERE_PEOPLE_ONLY, toxic_to_pets: false },
    { toxicity_description: FOOD_CROP, toxic_to_pets: true },
  ];
  for (const c of cases) {
    const line = toxicityLine(c)!;
    expect(line.hazard).toBe(true);
    expect(line.text.startsWith('⚠️ ')).toBe(true);
    expect(line.text.match(/⚠/g)).toHaveLength(1);
  }
});

test('an older server’s bare flag still warns, and no flag says nothing', () => {
  expect(toxicityLine({ toxic_to_pets: true })).toEqual({ text: '⚠️ Toxic to pets.', hazard: true });
  expect(toxicityLine({ toxicity_description: '', toxic_to_pets: null })).toBeNull();
  expect(toxicityLine({})).toBeNull();
});

test('Add plant styles the line by the sentence, not by the pet flag', () => {
  const src: string = require('fs').readFileSync(
    require('path').join(__dirname, '../screens/AddPlantScreen.tsx'), 'utf8');
  expect(src).toMatch(/toxicityLine\(selectedSpecies\)/);
  expect(src).not.toMatch(/toxic_to_pets \? styles\.hazard/);
  expect(src).not.toMatch(/toxic_to_pets \? '⚠/);
});
