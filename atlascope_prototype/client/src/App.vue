<script lang="js">
import geo from "geojs";
import { defineComponent, onMounted, ref, watch } from "vue";
import { listImageItems, fetchImageTileInfo, fetchImageFeatures } from "./api";
import drawFeatures from "./drawFeatures.js";


export default defineComponent({
  setup() {
    const images = ref([]);
    const currentImage = ref();
    const map = ref();
    const imageLayer = ref();
    const featureLayer = ref();
    const features = ref();
    const numFeatures = ref(0);

    function selectImage(images) {
      if (images.length){
        currentImage.value = images[0];
        imageLayer.value = undefined;
        featureLayer.value = undefined;
        features.value = undefined;
        numFeatures.value = 0;
        fetchImageTileInfo(currentImage.value).then((tileInfo) => {
          let params = geo.util.pixelCoordinateParams(
            '#map',
            tileInfo.sizeX,
            tileInfo.sizeY,
            tileInfo.tileWidth,
            tileInfo.tileHeight
          );
          map.value = geo.map(params.map);
          params.layer.url = `${currentImage.value.apiUrl}/item/${currentImage.value.girderId}/tiles/zxy/{z}/{x}/{y}`;
          imageLayer.value = map.value.createLayer('osm', params.layer);
          featureLayer.value = map.value.createLayer('feature', {
            zIndex: 1,
            features: ['line', 'marker']
            // clickToEdit: false,
          });
        })
        fetchImageFeatures(currentImage.value).then((data) => {
          features.value = data;

          // JSON implementation
          data.forEach((roi) => numFeatures.value += roi.features.length)

          // Vector implementation
          // numFeatures.value = data.length
        })
      }
    }

    onMounted(() => {
      listImageItems().then((data) => {
        images.value = data
      })
    });

    watch(features, () => drawFeatures(features.value, featureLayer.value))
    watch(featureLayer, () => drawFeatures(features.value, featureLayer.value))

    return {
      images,
      currentImage,
      selectImage,
      features,
      numFeatures,
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
    <v-navigation-drawer v-if="currentImage" location="right" app>
      <v-progress-linear v-if="!features" indeterminate absolute />
      <v-card-text>
        {{ features ? numFeatures : "Fetching" }} Features
      </v-card-text>
    </v-navigation-drawer>
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
