// The shape every translation must match: the English resource with every
// string leaf widened to `string`, so a missing or extra key in es/ is a
// type error rather than a blank on someone's screen.
export type Strings<T> = {
  [K in keyof T]: T[K] extends string ? string : Strings<T[K]>;
};

export type Language = 'en' | 'es';
