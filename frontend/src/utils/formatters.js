export function formatDate(isoString) {
  if (!isoString) return '--';
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(new Date(isoString));
}

export function formatCoordinates(lat, lng) {
  if (!lat || !lng) return 'Não informadas';
  return `${lat}, ${lng}`;
}