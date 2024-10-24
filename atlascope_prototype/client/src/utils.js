// from https://stackoverflow.com/a/30773300
export function metersPerPixel(latitude, zoomLevel) {
  var earthCircumference = 40075017;
  var latitudeRadians = latitude * (Math.PI / 180);
  return (
    (earthCircumference * Math.cos(latitudeRadians)) /
    Math.pow(2, zoomLevel + 8)
  );
}

// regl-scatterplot requires points to be normalized for performance
export function normalizePoints(points) {
  const xMin = Math.min(...points.map((p) => p.x));
  const xMax = Math.max(...points.map((p) => p.x));
  const yMin = Math.min(...points.map((p) => p.y));
  const yMax = Math.max(...points.map((p) => p.y));
  return points.map((p) => ({
    ...p,
    x: (p.x - xMin) / (xMax - p.x),
    y: (p.y - yMin) / (yMax - p.y),
  }));
}
