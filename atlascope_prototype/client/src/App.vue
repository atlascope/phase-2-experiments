<script lang="js">
import "leaflet/dist/leaflet.css";

import { defineComponent, ref, watch, computed } from "vue";
import VResizeDrawer from  '@wdns/vuetify-resize-drawer';
import { VTreeview } from 'vuetify/labs/VTreeview';
import { LMap, LTileLayer } from "@vue-leaflet/vue-leaflet";
import { CRS } from 'leaflet';
import LEllipse from "vue-leaflet-ellipse";

import { getImageTileInfo, getImageTileUrl, listCollections, listFolders, listItems } from "./api";
import { metersPerPixel } from "./utils";

export default defineComponent({
  components: {
    VResizeDrawer,
    VTreeview,
    LMap,
    LTileLayer,
    LEllipse,
  },
  setup() {
    // Data Tree
    const treeData = ref([{
      name: 'Girder Data',
      _id: 'root',
      _modelType: 'root',
      children: []
    }]);
    const openParents = ref([]);
    const activeImage = ref();
    const activeImageURL = computed(() => {
      if (activeImage.value?.length === 1) {
        return getImageTileUrl(activeImage.value[0])
      }
      return undefined;
    })

    // Map
    const map = ref(null);
    const crs = CRS.Simple;
    const center = ref();
    const zoom = ref(2);
    const maxZoom = ref();

    // Annotations
    const showFileUpload = ref(false);
    const annotationFile = ref();
    const currentAnnotation = ref();
    const annotationColor = ref('#00ff00');
    const elementListLength = ref(0);
    const elementList = computed(() => {
      if (ellipses.value) {
        const uniqueEllipses = ellipses.value.filter(
          (element, index) => ellipses.value.map((e) => e.id).indexOf(element.id) === index
        )
        const sortedBySelected = uniqueEllipses.toSorted((e1, e2) => {
          if (selectedElements.value.includes(e1.id) && selectedElements.value.includes(e2.id)) return e1.id - e2.id
          else if (selectedElements.value.includes(e1.id)) return -1
          else if (selectedElements.value.includes(e2.id)) return 1
          return e1.id - e2.id
        })
        return sortedBySelected.slice(0, elementListLength.value)
      } else {
        return []
      }
    });
    const selectedElements = ref([]);
    const ellipses = computed(() => {
      if (currentAnnotation.value?.elements) {
        return currentAnnotation.value.elements.map((element) => {
          const id = element.user?.id || -1;
          const position = crs.pointToLatLng(
            {x: element.center[0], y: element.center[1]},
            maxZoom.value,
          )
          const metersMultiplier = metersPerPixel(position.lat, maxZoom.value)
          const radius = [
            element.width / 2 * metersMultiplier,
            element.height / 2 * metersMultiplier,
          ]
          const details = [
            {key: 'center', value: element.center},
            {key: 'width', value: element.width},
            {key: 'height', value: element.height},
            {key: 'rotation', value: element.rotation},
          ]
          return {
            id,
            details,
            rotation: -element.rotation,
            position,
            radius,
            title: `Element ${element.user?.id}`,
            opacity: selectedElements.value.length && selectedElements.value.includes(id) ? 1 : 0.2,
          }
        }).toSorted((e1, e2) => e1.id - e2.id)
      } else {
        return []
      }
    })

    // Functions
    function updateChildren(root, parent_id, children) {
      children = children.map((child) => {
        if (child._modelType !== 'item') {
          child.children=[];
        }
        return child
      })
      if (root._id === parent_id) {
        root.children = children;
      } else {
        root.children = root.children.map(
          (child) => updateChildren(child, parent_id, children)
        )
      }
      return root;
    }

    async function loadChildren(item) {
      if (!item) return
      let loadFunc = null;
      if (item._modelType == 'root') {
        loadFunc = () => listCollections()
      }
      else if (item._modelType == 'collection') {
        loadFunc = () => listFolders(item._id)
      }
      else if (item._modelType == 'folder') {
        loadFunc = () => listItems(item._id)
      }
      if (loadFunc) {
        return loadFunc().then((data) => {
          treeData.value = [updateChildren(
            treeData.value[0],
            item._id,
            data
          )]
        })
      }
    }

    function submitAnnotationFile() {
      if (annotationFile.value) {
        elementListLength.value = 0
        selectedElements.value = [];
        currentAnnotation.value = undefined;
        const reader = new FileReader();
        reader.onload = (event) => {
          const contents = event.target.result;
          if (contents) {
            currentAnnotation.value = JSON.parse(contents);
            annotationFile.value = undefined;
            showFileUpload.value = false;
          }
        }
        reader.readAsText(annotationFile.value)
      }
    }

    async function resetView() {
      center.value = undefined;
      maxZoom.value = undefined;
      zoom.value = undefined;
      if (activeImage.value?.length === 1) {
        getImageTileInfo(activeImage.value[0]).then((info) => {
          zoom.value = 2;
          maxZoom.value = info.levels - 1;
          const maxCoord = crs.pointToLatLng(
            {x: info.sizeX, y: info.sizeY},
            maxZoom.value,
          )
          center.value = [
            maxCoord.lat / 2, maxCoord.lng / 2
          ]
        })
      }
    }

    async function expandElementList({ done }) {
      if (elementList.value.length === currentAnnotation.value?.elements.length) {
        done('empty');
      } else {
        elementListLength.value += 10
        done('ok');
      }
    }

    function flyToElement(element) {
      center.value = element.position;
      zoom.value = maxZoom.value;
    }

    function selectElement(element, event) {
      if (!event.originalEvent.shiftKey) selectedElements.value = []
      if (selectedElements.value.includes(element.id)) {
        selectedElements.value = selectedElements.value.filter((v) => v !== element.id)
      } else {
        selectedElements.value.push(element.id)
      }
    }

    // Watchers
    watch(openParents, () => {
      openParents.value.forEach((parent) => {
        if (!parent.children?.length) {
          loadChildren(parent);
        }
      })
    })

    watch(activeImage, () => {
      showFileUpload.value = false;
      annotationFile.value = undefined;
      currentAnnotation.value = undefined;
      elementListLength.value = 0;
      selectedElements.value = [];
      resetView();
    })

    return {
      treeData,
      openParents,
      activeImage,
      activeImageURL,
      map,
      crs,
      center,
      zoom,
      maxZoom,
      showFileUpload,
      annotationFile,
      submitAnnotationFile,
      currentAnnotation,
      annotationColor,
      elementList,
      selectedElements,
      expandElementList,
      ellipses,
      resetView,
      flyToElement,
      selectElement,
    };
  },
});
</script>

<template>
  <v-app>
    <VResizeDrawer>
      <v-treeview
        v-model:opened="openParents"
        v-model:activated="activeImage"
        :items="treeData"
        item-title="name"
        item-value="_id"
        density="compact"
        open-on-click
        activatable
        transition
        return-object
      >
      </v-treeview>
    </VResizeDrawer>
    <v-main style="width: 100%; height: 100%">
      <l-map
        v-if="activeImage && center"
        ref="map"
        :crs="crs"
        :zoom="zoom"
        :center="center"
        :zoomAnimation="true"
      >
        <v-btn
          icon="mdi-arrow-expand-all"
          class="map-button"
          style="left: 60px"
          @click="resetView"
        ></v-btn>
        <v-btn
          icon="mdi-upload"
          class="map-button"
          style="right: 10px"
          @click="showFileUpload = true"
        ></v-btn>
        <l-tile-layer
          v-if="maxZoom"
          :url="activeImageURL"
          :noWrap="true"
          :maxZoom="maxZoom"
          layer-type="base"
          name="ImageLayer"
        ></l-tile-layer>
        <l-ellipse
          v-for="ellipse in ellipses"
          :key="ellipse.id"
          :name="`${ellipse.id}`"
          :lat-lng="ellipse.position"
          :radius="ellipse.radius"
          :tilt="ellipse.rotation"
          :opacity="ellipse.opacity"
          :color="annotationColor"
          :visible="zoom > 6"
          @click="(event) => selectElement(ellipse, event)"
        />
      </l-map>
      <v-card-subtitle v-else class="pa-5">
        Select an Image from Girder to begin.
      </v-card-subtitle>
    </v-main>
    <VResizeDrawer v-if="currentAnnotation" location="right">
      <v-card-title class="pa-3">Annotation Options</v-card-title>
      <v-expansion-panels class="pl-6 pr-3">
        <v-expansion-panel>
          <v-expansion-panel-title>
            {{ currentAnnotation.elements.length }} annotation elements
          </v-expansion-panel-title>
          <v-expansion-panel-text class="py-0">
            <v-infinite-scroll
              :height="300"
              :onLoad="expandElementList"
              :items="elementList"
              style="width: 100%"
              empty-text="Loaded all elements."
            >
              <template v-for="element in elementList" :key="element.id">
                <v-expansion-panels>
                  <v-expansion-panel elevation="0">
                    <v-expansion-panel-title
                      class="pa-0"
                      :color="
                        selectedElements.includes(element.id)
                          ? annotationColor + '33'
                          : '#ffffff00'
                      "
                    >
                      <v-checkbox
                        v-model="selectedElements"
                        :value="element.id"
                        hide-details
                        density="compact"
                        @click.stop
                      ></v-checkbox>
                      <v-icon
                        icon="mdi-fit-to-screen"
                        @click.stop="flyToElement(element)"
                      ></v-icon>
                      {{ element.title }}
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <p v-for="detail in element.details" :key="detail.key">
                        {{ detail.key }}: {{ detail.value }}
                      </p>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </template>
            </v-infinite-scroll>
          </v-expansion-panel-text>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-title>
            Color
            <v-avatar
              :color="annotationColor"
              size="small"
              class="color-preview"
            />
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-color-picker v-model="annotationColor"></v-color-picker>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </VResizeDrawer>
    <v-dialog v-model="showFileUpload" width="500">
      <v-card class="pa-3">
        <v-btn
          flat
          icon="mdi-close"
          style="position: absolute; right: 5px"
          @click="showFileUpload = false"
        ></v-btn>
        <v-card-title>Upload Annotation File</v-card-title>
        <v-file-input
          v-model="annotationFile"
          accept=".json"
          label="Annotation File"
          show-size
        ></v-file-input>
        <v-card-actions>
          <v-btn @click="showFileUpload = false" color="red">Cancel</v-btn>
          <v-btn @click="submitAnnotationFile">Submit</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<style>
.main-area {
  position: absolute;
  top: 65px;
  height: calc(100% - 70px);
  width: 100%;
}
.map-button {
  position: absolute;
  top: 10px;
  /* leaflet uses z-index: 800 for zoom controls */
  z-index: 400;
}
.color-preview {
  position: absolute;
  top: 10px;
  right: 50px;
}
.v-list--slim .v-treeview-group.v-list-group {
  /* decrease tree indent */
  --prepend-width: 5px !important;
}
.v-expansion-panel-text__wrapper {
  padding: 0px 16px !important;
}
</style>
