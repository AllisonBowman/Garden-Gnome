import {
  formatDegrees, formatTemp, fromFahrenheit, getTempUnit, roundedTemp, setTempUnitForFormatting, unitSpoken,
} from './temperature';
import { forecastCaption, freezingLabel } from '../home/forecastBars';

afterEach(() => setTempUnitForFormatting('F'));

test('°F by default, written as the app writes it', () => {
  expect(getTempUnit()).toBe('F');
  expect(formatTemp(35)).toBe('35°F');
  expect(formatDegrees(54.4)).toBe('54°');
  expect(freezingLabel()).toBe('32°F');
});

test('°C converts every reading the app writes itself', () => {
  setTempUnitForFormatting('C');
  expect(fromFahrenheit(212)).toBeCloseTo(100);
  expect(formatTemp(32)).toBe('0°C');
  expect(formatTemp(14)).toBe('-10°C');
  expect(roundedTemp(50)).toBe('10');
  expect(freezingLabel()).toBe('0°C');
  expect(forecastCaption(false)).toBe('Highs and lows in °C.');
  expect(unitSpoken()).toBe('degrees Celsius');
});
