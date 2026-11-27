// The app's one navigator and every screen on it (build spec section 6).
//
// There is no tab bar: one native stack opens on Home, and everything else is
// reached from there. Screen names are fixed by the spec so the packages that
// build Land, Season, ZoneMap and PropertySetup can link to each other and to
// the screens that were here before. Pure types, no runtime imports, so any
// screen can import this without pulling App.tsx in.

/** What Add Plant may be opened with: `growingAreaId` preselects where the
 *  plant goes, set when it is opened from an area's own screen. */
export type AddPlantParams = { growingAreaId?: number } | undefined;

/** A species, and (when it was opened from an area's candidates or the
 *  Almanac's area filter) the area it was being read against, whose full
 *  findings the page then shows. */
export type SpeciesDetailParams = { speciesId: number; growingAreaId?: number };

/** The Almanac, and the growing area to open it narrowed to: set when it is
 *  opened from that area's screen to see the rest of its candidates. */
export type AlmanacParams = { growingAreaId?: number } | undefined;

/** Property setup. With no `propertyId` it makes a new property; with one it
 *  goes back over that property's pin and lot contents. */
export type PropertySetupParams = { propertyId?: number } | undefined;

/** The site profile of one property, opened at one zone when `zoneId` is
 *  set, or at one value when `field` is set (a Home land line). */
export type LandParams = { propertyId: number; zoneId?: number; field?: string };

/** The zone map of one property, opened on one zone when `zoneId` is set. */
export type ZoneMapParams = { propertyId: number; zoneId?: number };

/** The seasonal plan of one property, scrolled to one event when
 *  `eventKey` is set (a Home "This week" or "The season ahead" row). */
export type SeasonParams = { propertyId: number; eventKey?: string };

export type RootStackParamList = {
  Home:          undefined;
  PropertySetup: PropertySetupParams;
  Land:          LandParams;
  ZoneMap:       ZoneMapParams;
  Season:        SeasonParams;
  Spaces:        undefined;
  SpaceDetail:   { growingAreaId: number; name?: string };
  Plants:        undefined;
  PlantDetail:   { plantId: number };
  AddPlant:      AddPlantParams;
  CaptureGarden: undefined;
  Species:       undefined;
  SpeciesDetail: SpeciesDetailParams;
  /** The catalog narrowed to a growing area. Not in the spec's table; it
   *  was reached from Species, Census and an area before, and still is. */
  Almanac:       AlmanacParams;
  Settings:      undefined;
  Census:        undefined;
  /** The "How we know" sheet: sources, method and confidence for the
   *  screen that opened it (howWeKnow/store.ts holds what it shows). */
  HowWeKnow:     undefined;
};

export type ScreenName = keyof RootStackParamList;
