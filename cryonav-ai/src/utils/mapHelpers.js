/**
 * Map coordinate and distance calculation helpers for CryoNav AI
 */

// Convert degrees to radians
const toRad = (deg) => (deg * Math.PI) / 180;
const toDeg = (rad) => (rad * 180) / Math.PI;

/**
 * Calculates Great Circle distance between two [lat, lon] coordinates in kilometers (Haversine formula)
 */
export function calculateDistance(coord1, coord2) {
  if (!coord1 || !coord2) return 0;
  const [lat1, lon1] = coord1;
  const [lat2, lon2] = coord2;
  const R = 6371; // Earth radius in km

  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return parseFloat((R * c).toFixed(1));
}

/**
 * Calculates initial bearing (heading) in degrees from point A to point B
 */
export function calculateBearing(coord1, coord2) {
  if (!coord1 || !coord2) return 0;
  const [lat1, lon1] = coord1;
  const [lat2, lon2] = coord2;
  const phi1 = toRad(lat1);
  const phi2 = toRad(lat2);
  const deltaLambda = toRad(lon2 - lon1);

  const y = Math.sin(deltaLambda) * Math.cos(phi2);
  const x =
    Math.cos(phi1) * Math.sin(phi2) -
    Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda);
  const theta = Math.atan2(y, x);
  return (toDeg(theta) + 360) % 360;
}

/**
 * Formats lat/lon into navigational notation (e.g., "65°00'S, 64°00'W")
 */
export function formatCoordinates(coord) {
  if (!coord || coord.length < 2) return '--';
  const [lat, lon] = coord;
  const latHem = lat >= 0 ? 'N' : 'S';
  const lonHem = lon >= 0 ? 'E' : 'W';
  const latAbs = Math.abs(lat);
  const lonAbs = Math.abs(lon);

  const latDeg = Math.floor(latAbs);
  const latMin = Math.round((latAbs - latDeg) * 60);
  const lonDeg = Math.floor(lonAbs);
  const lonMin = Math.round((lonAbs - lonDeg) * 60);

  return `${latDeg}°${latMin < 10 ? '0' : ''}${latMin}'${latHem}, ${lonDeg}°${lonMin < 10 ? '0' : ''}${lonMin}'${lonHem}`;
}

/**
 * Generates an uncertainty cone polygon for iceberg drift prediction
 */
export function generateUncertaintyCone(startCoord, predictedPoints) {
  if (!predictedPoints || predictedPoints.length === 0) return [];
  const cone = [[startCoord[0], startCoord[1]]];
  
  // Left wing
  for (let i = 0; i < predictedPoints.length; i++) {
    const spread = (i + 1) * 0.04;
    cone.push([predictedPoints[i][0] + spread, predictedPoints[i][1] - spread]);
  }
  // Right wing backwards
  for (let i = predictedPoints.length - 1; i >= 0; i--) {
    const spread = (i + 1) * 0.04;
    cone.push([predictedPoints[i][0] - spread, predictedPoints[i][1] + spread]);
  }
  cone.push([startCoord[0], startCoord[1]]);
  return cone;
}
