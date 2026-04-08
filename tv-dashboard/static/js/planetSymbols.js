/** Unicode astronomy symbols for classical planets */
export const PLANET_SYM = {
  Sun: '☉',
  Moon: '☽',
  Mercury: '☿',
  Venus: '♀',
  Mars: '♂',
  Jupiter: '♃',
  Saturn: '♄',
  Uranus: '♅',
  Neptune: '♆',
  Pluto: '♇',
};

export function planetSym(name) {
  return PLANET_SYM[name] || (name && name[0]) || '?';
}
