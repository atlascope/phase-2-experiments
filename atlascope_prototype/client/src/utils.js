import { listItemFiles, getItemFileUrl } from "./api";
import { asyncBufferFromUrl, parquetRead } from "hyparquet";

export async function fetchNuclei(parquetItem) {
  const start = new Date();
  let nuclei = undefined;
  if (parquetItem) {
    const files = await listItemFiles(parquetItem._id);
    if (files && files.length) {
      const url = getItemFileUrl(files[0]._id);
      await parquetRead({
        file: await asyncBufferFromUrl({ url }),
        rowFormat: "object",
        onComplete: (data) => {
          nuclei = data.map((row, id) => {
            const roi = {};
            row.roiname
              .split("_")
              .slice(2)
              .forEach((component) => {
                let [key, value] = component.split("-");
                roi[key] = parseInt(value);
              });
            const x = row["Unconstrained.Identifier.CentroidX"] * 2 + roi.left;
            const y = row["Unconstrained.Identifier.CentroidY"] * 2 + roi.top;
            const width = row["Size.MinorAxisLength"] * 2;
            const height = row["Size.MajorAxisLength"] * 2;
            const rotation = 0 - row["Orientation.Orientation"];
            return {
              id,
              title: `Element ${id}`,
              details: row,
              x,
              y,
              width,
              height,
              radius: Math.max(width, height),
              rotation: width > height ? rotation : rotation + Math.PI / 2,
              aspectRatio: Math.min(width, height) / Math.max(width, height),
            };
          });
        },
      });
    }
  }
  const end = new Date();
  console.log(
    "Retrieved feature vector data in ",
    (end - start) / 1000,
    " seconds."
  );
  return nuclei;
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

export function clamp(value, range) {
  return Math.max(Math.min(value, Math.max(...range)), Math.min(...range));
}

export function hexToRgb(hex) {
  // from https://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb
  var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? [
        parseInt(result[1], 16),
        parseInt(result[2], 16),
        parseInt(result[3], 16),
      ]
    : null;
}

export function rgbToHex([r, g, b]) {
  // from https://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb
  return "#" + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1);
}
