<script lang="js">
import geo from "geojs";
import { defineComponent, onMounted, ref } from "vue";
import { listImageItems, fetchImageTileInfo } from "./api";

export default defineComponent({
  setup() {
    const images = ref([]);
    const map = ref();

    function selectImage(images) {
      if (images.length){
        const image = images[0]
        fetchImageTileInfo(image).then((tileInfo) => {
          let params = geo.util.pixelCoordinateParams(
            '#map',
            tileInfo.sizeX,
            tileInfo.sizeY,
            tileInfo.tileWidth,
            tileInfo.tileHeight
          );
          map.value = geo.map(params.map);
          params.layer.url = `${image.apiUrl}/item/${image.id}/tiles/zxy/{z}/{x}/{y}`;
          const imageLayer = map.value.createLayer('osm', params.layer);
          return imageLayer;
        })
      }
    }

    onMounted(() => {
      listImageItems().then((data) => {
        images.value = data
      })
    });

    return {
      images,
      selectImage,
    };
  },
});
</script>

<template>
  <v-app>
    <v-navigation-drawer permanent app>
      <v-card-text v-if="!images.length">No images found.</v-card-text>
      <v-list @update:selected="selectImage" :rounded="true">
        <v-list-item
          v-for="image in images"
          :value="image"
          :key="image.id"
          :title="image.name"
          v-tooltip="image.name"
        >
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
    <v-main>
      <div id="map" style="height: 100%"></div>
    </v-main>
  </v-app>
</template>

<style scoped>
.main-area {
  position: absolute;
  top: 65px;
  height: calc(100% - 70px);
  width: 100%;
}
</style>
