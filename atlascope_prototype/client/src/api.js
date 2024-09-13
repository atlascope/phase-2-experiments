import axios from "axios";

export async function listImageItems() {
  const url = `${process.env.VUE_APP_API_ROOT}/images`;
  return (await axios.get(url)).data;
}

export async function fetchImageTileInfo(image) {
  const url = `${image.apiUrl}/item/${image.girderId}/tiles`;
  return (await axios.get(url)).data;
}

export async function fetchImageFeatures(image) {
  const url = `${process.env.VUE_APP_API_ROOT}/images/${image.id}/features`;
  return (await axios.get(url)).data;
}
