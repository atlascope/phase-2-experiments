<script lang="js">
import { defineComponent, ref, watch, computed, nextTick } from "vue";
import VResizeDrawer from  '@wdns/vuetify-resize-drawer';
import { VTreeview } from 'vuetify/labs/VTreeview';
import geo from 'geojs';
import createScatterplot from 'regl-scatterplot';


import {
  getImageTileInfo,
  getImageTileUrl,
  listCollections,
  listFolders,
  listItems,
  listAnnotations,
  getAnnotationContents,
} from "./api";
import { getQuadCoords, normalizePoints } from "./utils";

export default defineComponent({
  components: {
    VResizeDrawer,
    VTreeview,
  },
  setup() {
    const loading = ref(false);

    // Data Tree
    const treeData = ref([{
      name: 'Girder Data',
      _id: 'root',
      _modelType: 'root',
      children: []
    }]);
    const openParents = ref([]);
    const activeImage = ref();

    // Map
    const map = ref(null);
    const center = ref();
    const zoom = ref(2);
    const maxZoom = ref();

    // Annotations
    const availableAnnotations = ref([]);
    const annotationLayer = ref();
    const showEllipses = ref(true);
    const showFileUpload = ref(false);
    const annotationFile = ref();
    const currentAnnotation = ref();
    const openPanel = ref([]);
    const annotationColor = ref('#00ff00');
    const selectedColor = ref('#0000ff');
    const ellipses = computed(() => {
      if (currentAnnotation.value?.elements) {
        return currentAnnotation.value.elements.map((element) => {
          const id = element.user?.id || -1;
          return {
            id,
            title: `Element ${id}`,
            details: [
              {key: 'center', value: element.center},
              {key: 'width', value: element.width},
              {key: 'height', value: element.height},
              {key: 'rotation', value: element.rotation},
            ],
            dimReductionPoint: {
              id,
              x: element.user?.x,
              y: element.user?.y,
            },
            center: {
              x: element.center[0],
              y: element.center[1],
            },
            coords: getQuadCoords(element),
            opacity: selectedElements.value.includes(id) ? 1 : 0.2,
            color: selectedElements.value.includes(id) ? selectedColor.value : annotationColor.value
          }
        }).toSorted((e1, e2) => e1.id - e2.id)
      } else {
        return []
      }
    })
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
    const normalizedPoints = ref();
    const scatterplot = ref();

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
        loading.value = true;
        elementListLength.value = 0
        selectedElements.value = [];
        currentAnnotation.value = undefined;
        const reader = new FileReader();
        reader.onload = (event) => {
          const contents = event.target.result;
          if (contents) {
            currentAnnotation.value = {
              _id: undefined,
              title: annotationFile.value.name,
              subtitle: 'Uploaded file; not persistent in Girder',
              elements: JSON.parse(contents).elements
            }
            availableAnnotations.value.push(currentAnnotation.value)
            annotationFile.value = undefined;
            showFileUpload.value = false;
            loading.value = false;
          }
        }
        reader.readAsText(annotationFile.value)
      }
    }

    function initView() {
      loading.value = true;
      center.value = undefined;
      maxZoom.value = undefined;
      zoom.value = undefined;
      map.value = undefined;
      annotationLayer.value = undefined;
      if (activeImage.value?.length === 1) {
        let image = activeImage.value[0]
        listAnnotations(image._id).then((annotations) => {
          availableAnnotations.value = annotations.map((a) => {
            return {
              _id: a._id,
              title: a.annotation.name,
              subtitle: a.annotation.description,
              elements: [],
            }
          });
        })
        getImageTileInfo(image).then((info) => {
          maxZoom.value = info.levels - 1;
          let params = geo.util.pixelCoordinateParams(
            '#map',
            info.sizeX,
            info.sizeY,
            info.tileWidth,
            info.tileHeight
          );
          map.value = geo.map(params.map);
          center.value = map.value.center();
          zoom.value = map.value.zoom();
          params.layer.url = getImageTileUrl(image);
          map.value.createLayer('osm', params.layer);
          annotationLayer.value = map.value.createLayer('feature', {
            features: ['line']
          });
          map.value.draw();
          // loading.value = false;
        })
      }
    }

    function resetView() {
      if (map.value && center.value && zoom.value) {
        map.value.zoom(zoom.value).center(center.value)
      }
    }

    function drawEllipses() {
      if (!annotationLayer.value) return;
      loading.value = true;
      annotationLayer.value.clear()
      if (ellipses.value.length && showEllipses.value) {
        annotationLayer.value.createFeature('line')
        .data(ellipses.value)
        .line((element) => element.coords)
        .style({
          strokeWidth: 4,
          closed: true,
          strokeColor:  (_vertex, _vIndex, item) => item.color,
          strokeOpacity: (_vertex, _vIndex, item) => item.opacity,
        })
        .geoOn(geo.event.feature.mousedown, (e) => {
          selectElement(e.data, e.sourceEvent)
        })
        .draw()
      } else {
        annotationLayer.value.draw()
      }
      loading.value = false;
    }

    function flyToElement(element) {
      if (map.value && element.center && maxZoom.value) {
        map.value.zoom(maxZoom.value).center(element.center);
      }
    }

    async function expandElementList({ done }) {
      // implementation complies with Vuetify's Infinite Scroll component API
      if (elementList.value.length === currentAnnotation.value?.elements.length) {
        done('empty');
      } else {
        elementListLength.value += 10
        done('ok');
      }
    }

    function selectElement(element, event) {
      if (!event.modifiers.shift) selectedElements.value = []
      if (selectedElements.value.includes(element.id)) {
        selectedElements.value = selectedElements.value.filter((v) => v !== element.id)
      } else {
        selectedElements.value = [
          ...selectedElements.value, element.id
        ]
      }
    }

    function drawScatter() {
      const canvas = document.getElementById('scatter-canvas')
      if (canvas) {
        const { width, height } = canvas.getBoundingClientRect();
        scatterplot.value = createScatterplot({
          canvas,
          width,
          height,
          pointSize: 5,
        });
        scatterplot.value.clear();
        normalizedPoints.value = normalizePoints(ellipses.value.map((ellipse) => {
          return ellipse.dimReductionPoint
        }))
        const drawPoints = normalizedPoints.value.map((p) => [
          p.x, p.y,
          selectedElements.value.length && selectedElements.value.includes(p.id) ? 1 : 0.2,
        ])
        const selectedIndexes = normalizedPoints.value.map((p, i) => {
          if (selectedElements.value.includes(p.id)) return i
          return undefined
        }).filter((i) => i)
        scatterplot.value.draw(drawPoints, {
          select: selectedIndexes,
        });
        scatterplot.value.set({
          opacityBy: 'valueA',
          pointColor: annotationColor.value,
          pointSize: 6,
        })
        scatterplot.value.zoomToArea(
          { x: 0, y: 0, width: 2, height: 2 },
          { transition: true }
        );
        scatterplot.value.subscribe('select', ({ points }) => {
          // regl-scatterplot returns point indexes
          selectedElements.value = normalizedPoints.value.map((p, i) => {
            if (points.includes(i)) return p.id
            return undefined
          }).filter((id) => id);
        })
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
      initView();
    })

    watch(openPanel, () => {
      if (openPanel.value === 'scatter') {
        nextTick().then(drawScatter)
      }
    })

    watch(selectedElements, () => {
      if (scatterplot.value) {
        // regl-scatterplot requires point indexes
        const selectedIndexes = normalizedPoints.value.map((p, i) => {
          if (selectedElements.value.includes(p.id)) return i
          return undefined
        }).filter((i) => i)
        scatterplot.value.select(selectedIndexes, {preventEvent: true})
      }
    })

    watch(currentAnnotation, () => {
      if (currentAnnotation.value?._id) {
        loading.value = true;
        getAnnotationContents(currentAnnotation.value._id).then((contents) => {
          currentAnnotation.value.elements = contents.annotation.elements
          loading.value = false;
        })
      }
      if (openPanel.value === 'scatter') {
        nextTick().then(drawScatter)
      }
    })

    watch(ellipses, drawEllipses)

    watch(showEllipses, drawEllipses)

    return {
      loading,
      treeData,
      openParents,
      activeImage,
      availableAnnotations,
      showFileUpload,
      showEllipses,
      annotationFile,
      submitAnnotationFile,
      currentAnnotation,
      openPanel,
      annotationColor,
      selectedColor,
      elementList,
      selectedElements,
      expandElementList,
      resetView,
      flyToElement,
      selectElement,
    };
  },
});
</script>

<template>
  <v-app>
    <v-progress-linear v-if="loading" indeterminate />
    <VResizeDrawer name="left">
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
      <v-card-subtitle v-if="!activeImage" class="pa-5">
        Select an Image from Girder to begin.
      </v-card-subtitle>
      <div id="map" style="height: 100%">
        <v-btn
          v-if="activeImage"
          icon="mdi-arrow-expand-all"
          class="map-button"
          style="left: 10px"
          @click="resetView"
        ></v-btn>
      </div>
    </v-main>
    <VResizeDrawer
      v-if="availableAnnotations.length"
      location="right"
      name="right"
    >
      <v-card-title class="pa-3">Annotation Options</v-card-title>
      <v-select
        v-model="currentAnnotation"
        :items="availableAnnotations"
        label="Current Annotation"
        item-props
        return-object
        hide-details
        class="pa-3"
      >
        <template v-slot:append>
          <v-icon icon="mdi-upload" @click="showFileUpload = true"></v-icon>
        </template>
      </v-select>
      <v-switch
        v-if="currentAnnotation"
        v-model="showEllipses"
        label="Show Ellipses"
        class="my-0 px-6"
        hide-details
      />
      <v-expansion-panels
        v-if="currentAnnotation"
        v-model="openPanel"
        class="pl-6 pr-3"
      >
        <v-expansion-panel value="elements">
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
                          ? selectedColor + '11'
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
        <v-expansion-panel value="color">
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
        <v-expansion-panel
          title="Dimensionality Reduction Results"
          value="scatter"
        >
          <v-expansion-panel-text>
            <canvas id="scatter-canvas"></canvas>
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
        <v-progress-linear v-if="loading" indeterminate />
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
#scatter-canvas {
  width: 100%;
  height: calc(100vh - 250px);
}
.v-list--slim .v-treeview-group.v-list-group {
  /* decrease tree indent */
  --prepend-width: 5px !important;
}
.v-expansion-panel-text__wrapper {
  padding: 0px 16px !important;
}
</style>
