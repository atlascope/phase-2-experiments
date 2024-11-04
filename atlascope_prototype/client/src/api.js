import axios from "axios";

const girderClient = axios.create({
  baseURL: `${process.env.VUE_APP_API_ROOT}`,
});

export async function listCollections() {
  const url = `${process.env.VUE_APP_API_ROOT}/collection`;
  return (await girderClient.get(url)).data;
}

export async function listFolders(collectionId) {
  const url = `${process.env.VUE_APP_API_ROOT}/folder?parentType=collection&parentId=${collectionId}`;
  return (await girderClient.get(url)).data;
}

export async function listItems(folderId) {
  const url = `${process.env.VUE_APP_API_ROOT}/item?folderId=${folderId}`;
  return (await girderClient.get(url)).data;
}

export async function listAnnotations(itemId) {
  const url = `${process.env.VUE_APP_API_ROOT}/annotation/?itemId=${itemId}`;
  return (await girderClient.get(url)).data;
}

export async function getImageTileInfo(image) {
  const url = `${process.env.VUE_APP_API_ROOT}/item/${image._id}/tiles`;
  return (await girderClient.get(url)).data;
}

export function getImageTileUrl(image) {
  return `${process.env.VUE_APP_API_ROOT}/item/${image._id}/tiles/zxy/{z}/{x}/{y}`;
}

export async function getAnnotationContents(annotationId) {
  const url = `${process.env.VUE_APP_API_ROOT}/annotation/${annotationId}`;
  return (await girderClient.get(url)).data;
}
