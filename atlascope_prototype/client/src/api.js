import axios from "axios";

export async function listCollections() {
  const url = `${process.env.VUE_APP_API_ROOT}/collection`;
  return (await axios.get(url)).data;
}

export async function listFolders(collectionId) {
  const url = `${process.env.VUE_APP_API_ROOT}/folder?parentType=collection&parentId=${collectionId}`;
  return (await axios.get(url)).data;
}

export async function listItems(folderId) {
  const url = `${process.env.VUE_APP_API_ROOT}/item?folderId=${folderId}`;
  return (await axios.get(url)).data;
}
