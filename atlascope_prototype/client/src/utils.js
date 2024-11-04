export function getQuadCoords(element) {
  const xRadius = element.width / 2;
  const yRadius = element.height / 2;
  return [
    [element.center[0] - xRadius, element.center[1] - yRadius],
    [element.center[0] + xRadius, element.center[1] - yRadius],
    [element.center[0] + xRadius, element.center[1] + yRadius],
    [element.center[0] - xRadius, element.center[1] + yRadius],
    [element.center[0] - xRadius, element.center[1] - yRadius],
  ].map((vertex) => ({ x: vertex[0], y: vertex[1] }));
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
