import {
  listItems,
  listSubFolders,
  listItemFiles,
  getFileContents,
} from "./api";

const LIST_LIMIT = 50;

export async function fetchFeatureVectors(caseFolder) {
  const start = new Date();
  const metaItems = [];
  const propItems = [];
  const subFolders = await listSubFolders(caseFolder._id);
  await Promise.all(
    subFolders.map(async (subFolder) => {
      let items = Array(LIST_LIMIT);
      let offset = 0;
      while (items.length == LIST_LIMIT) {
        items = await listItems(subFolder._id, offset);
        offset += items?.length || 0;
        if (subFolder.name === "nucleiMeta") {
          metaItems.push(...items);
        } else if (subFolder.name === "nucleiProps") {
          propItems.push(...items);
        }
      }
    })
  );
  await Promise.all(
    metaItems.map(async (metaItem) => {
      const propItem = propItems.find((i) => i.name === metaItem.name);
      const metaFiles = await listItemFiles(metaItem._id);
      const propFiles = await listItemFiles(propItem._id);
      if (metaFiles.length && propFiles.length) {
        const metaContents = await getFileContents(metaFiles[0]._id);
        const propContents = await getFileContents(propFiles[0]._id);
        const meta = metaContents.split("\n").map((line) => line.split(","));
        const prop = propContents.split("\n").map((line) => line.split(","));
        console.log(meta.length, prop.length);
        // const nuclei = {};
        [meta, prop].forEach((group) => {
          const columnHeaders = group[0];
          group.slice(1).forEach((row) => {
            const attrs = Object.fromEntries(
              row.map((v, i) => {
                return [columnHeaders[i], v];
              })
            );
            console.log(attrs);
          });
          // console.log(columnHeaders, group.slice(1));
        });
      }
    })
  );
  const end = new Date();
  console.log(
    "Retrieved feature vector data in ",
    (end - start) / 1000,
    " seconds."
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
