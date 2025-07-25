<script lang="js">
import { defineComponent, ref, watch, nextTick } from "vue";
import VResizeDrawer from  '@wdns/vuetify-resize-drawer';
import { VTreeview } from 'vuetify/labs/VTreeview';
import geo from 'geojs';
import createScatterplot from 'regl-scatterplot';
import debounce from 'lodash/debounce';
import colorbrewer from 'colorbrewer';
import { createColorMap, linearScale } from "@colormap/core";

import {
  getImageTileInfo,
  getImageTileUrl,
  listCollections,
  listCollectionFolders,
  listSubFolders,
  listItems,
} from "./api";
import { fetchNuclei, fetchResult, normalizePoints, clamp, hexToRgb, rgbToHex } from "./utils";

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
    const featureLayer = ref();
    const uiLayer = ref();
    const colorLegend = ref();
    const numVisible = ref(0);

    // Data Structures
    const nuclei = ref([]);
    const elementList = ref([]);
    const selectedElements = ref([]);

    // Scatter
    const availableResults = ref([]);
    const currentResult = ref();
    const loadingScatter = ref(false);
    const normalizedPoints = ref();
    const scatterplot = ref();

    // Options
    const showEllipses = ref(true);
    const openPanel = ref([]);
    const nucleiColors = ref();
    const featureColor = ref('#00ff00');
    const selectedColor = ref('#0000ff');
    const constantColor = ref(true);
    const colorByAttribute = ref();
    const colormapType = ref();
    const colormapName = ref();

    // Functions
    function updateChildren(root, parent_id, children) {
      children = children.map((child) => {
        if (child._modelType !== 'item') {
          child.children = [];
        }
        return child
      })
      if (root._id === parent_id) {
        root.children = children;
        root.image = root.children.find((c) => c.name.endsWith('.svs'));
        root.results = root.children.filter((c) => c.name.toLowerCase().includes('umap') || c.name.toLowerCase().includes('tsne'))
        root.parquet = root.children.find((c) => c.name.endsWith('.parquet') && !root.results.includes(c))
        if (root.image) {
          root.children = undefined;
        }
      } else if (root.children) {
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
        loadFunc = () => listCollectionFolders(item._id)
      }
      else if (item._modelType == 'folder') {
        loadFunc = () => {
          return Promise.all([listSubFolders(item._id), listItems(item._id)]).then(
            ([folders, items]) => [...folders, ...items]
          )
        }
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

    function initView() {
      center.value = undefined;
      maxZoom.value = undefined;
      zoom.value = undefined;
      map.value = undefined;
      featureLayer.value = undefined;
      if (activeImage.value?.length === 1) {
        const caseFolder = activeImage.value[0];
        loading.value = true;
        fetchNuclei(caseFolder.parquet).then((data) => {
          if (data)  nuclei.value = data;
          loading.value = false;
        })
        availableResults.value = caseFolder.results.map((result) => {
          return {
            _id: result._id,
            name: result.name.replace(caseFolder.name, '').replace('.parquet', '').trim(),
            metadata: result.meta,
          }
        });
        const image = caseFolder.image;
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
          map.value.geoOn(geo.event.pan, debounce(updateNumVisible, 500))
          center.value = map.value.center();
          zoom.value = map.value.zoom();
          params.layer.url = getImageTileUrl(image);
          map.value.createLayer('osm', params.layer);
          featureLayer.value = map.value.createLayer('feature', {
            features: ['marker']
          });
          uiLayer.value = map.value.createLayer('ui');
          colorLegend.value = uiLayer.value.createWidget(
            'colorLegend', {
              position: {
                bottom: 10,
                left: 10,
                right: 10,
              },
              ticks: 10,
              width: 1000,
            }
          )
          map.value.draw();
        })
      }
    }

    function resetView() {
      if (map.value && center.value && zoom.value) {
        map.value.zoom(zoom.value).center(center.value)
      }
    }

    function getColormap() {
      if (colormapName.value && colorByAttribute.value) {
        const allValues = [... new Set(
          nuclei.value.map((nucleus) => nucleus.details[colorByAttribute.value])
        )]
        const numeric = !allValues.some((v) => typeof v === 'string');
        const availableSets = colorbrewer[colormapName.value];
        const availableSetLengths = Object.keys(availableSets).map((v) => parseInt(v))
        const numColors = clamp(allValues.length, availableSetLengths)
        const colors = availableSets[numColors].map((c) => hexToRgb(c));
        let colormap = undefined;
        let domain = undefined;
        if (numeric) {
          domain = [Math.min(...allValues), Math.max(...allValues)];
          colormap = (v) => {
            const [r, g, b] = createColorMap(
              colors.map((c) => [c.r, c.g, c.b]),
              linearScale(domain, [0, 1])
            )(v);
            return {r, g, b}
          };
        } else {
          colormap = (v) => colors[clamp(allValues.indexOf(v), [0, numColors])]
        }
        colorLegend.value.categories([{
          name: colorByAttribute.value,
          type: allValues.length > numColors ? 'continuous' : 'discrete',
          scale: numeric ? 'linear' : 'ordinal',
          domain: numeric ? domain : allValues,
          colors: colors.map((c) => rgbToHex(c))
        }]);
        return colormap;
      } else {
        colorLegend.value.categories([]);
        return undefined;
      }
    }

    function drawEllipses() {
      if (!featureLayer.value) return;
      loading.value = true;
      featureLayer.value.clear()
      if (nuclei.value.length) {
        const feature = featureLayer.value.createFeature('marker')
        .data(nuclei.value)
        .geoOn(geo.event.feature.mouseclick, (e) => {
          selectElement(e.data, e.sourceEvent)
        });
        feature.style({
          radius: (item) => item.width / (2 ** (maxZoom.value + 1)),
          rotation: (item) => item.rotation,
          symbolValue: (item) => item.aspectRatio,
          symbol: geo.markerFeature.symbols.ellipse,
          scaleWithZoom: geo.markerFeature.scaleMode.fill,
          rotateWithMap: true,
          strokeWidth: 4,
          strokeOffset: 1,
          strokeOpacity: 1,
          fillOpacity: 0,
        })
        updateEllipses();
        feature.draw();
      } else {
        featureLayer.value.draw()
      }
      loading.value = false;
    }

    function updateEllipses() {
      const feature = featureLayer.value?.features()[0];
      if (feature) {
        const colormap = getColormap();
        feature.visible(showEllipses.value);
        if (showEllipses.value) {
          const featureColorRGB = hexToRgb(featureColor.value);
          const selectedColorRGB = hexToRgb(selectedColor.value);
          nucleiColors.value = nuclei.value.map((nucleus) => {
            if (selectedElements.value.includes(nucleus.id)) {
              return selectedColorRGB;
            }
            if (colormap) {
              return colormap(nucleus.details[colorByAttribute.value]);
            }
            return featureColorRGB;
          });
          const styles = {
            strokeColor: nucleiColors.value
          };
          feature.updateStyleFromArray(styles, null, true);
        }
      }
    }

    function flyToElement(element) {
      if (map.value && element.x !== undefined && maxZoom.value) {
        map.value.zoom(maxZoom.value).center({x: element.x, y: element.y});
      }
    }

    function updateNumVisible() {
      if (featureLayer.value && nuclei.value.length && showEllipses.value) {
        const feature = featureLayer.value.features()[0];
        const polySearch = feature.polygonSearch(map.value.corners());
        numVisible.value = polySearch.found?.length;
      } else {
        numVisible.value = 0
      }
    }

    async function expandElementList({ done }) {
      // implementation complies with Vuetify's Infinite Scroll component API
      if (!nuclei.value || elementList.value.length === nuclei.value.length) {
        done('empty');
      } else {
        if (nuclei.value) {
          elementList.value = nuclei.value.slice(0, elementList.value.length + 10)
        }
        done('ok');
      }
    }

    function selectElement(element, event) {
      if (selectedElements.value.includes(element.id)) {
        selectedElements.value = selectedElements.value.filter((v) => v !== element.id)
      } else if (event.modifiers.shift) {
        selectedElements.value = [
          ...selectedElements.value, element.id
        ]
      } else {
        selectedElements.value = [element.id];
      }
    }

    function drawScatter() {
      if (currentResult.value?.contents) {
        const canvas = document.getElementById('scatter-canvas')
        if (canvas) {
          const { width, height } = canvas.getBoundingClientRect();
          scatterplot.value = createScatterplot({
            canvas,
            width,
            height,
            pointSize: 5,
            pointScaleMode: 'constant',
            lassoOnLongPress: true,
          });
          scatterplot.value.clear();
          normalizedPoints.value = normalizePoints(currentResult.value.contents);
          const drawPoints = normalizedPoints.value.map((p) => [p.x, p.y, p.id])
          const selectedIndexes = normalizedPoints.value.map((p, i) => {
            if (selectedElements.value.includes(p.id)) return i
            return undefined
          }).filter((i) => i)
          scatterplot.value.draw(drawPoints, {
            select: selectedIndexes,
          });
          let colorset = nucleiColors.value;
          if (!colorset || colorset.length < drawPoints.length) {
            colorset = Array(drawPoints.length).fill(featureColor.value);
          } else {
            colorset = colorset.map((c) => rgbToHex(c));
          }
          scatterplot.value.set({
            colorBy: 'valueA',
            pointColor: colorset,
            pointSize: 6,
          })
          scatterplot.value.zoomToArea(
            { x: 0, y: 0, width: 2, height: 2 },
            { transition: true }
          );
          const updateSelectionFunction = ({ points }) => {
            // regl-scatterplot returns point indexes
            selectedElements.value = normalizedPoints.value.map((p, i) => {
              if (points.includes(i)) return p.id
              return undefined
            }).filter((id) => id);
          }
          scatterplot.value.subscribe('select', updateSelectionFunction)
          scatterplot.value.subscribe('deselect', () => updateSelectionFunction({points: []}))
          loadingScatter.value = false;
        }
      }
    }

    // Watchers
    watch(openParents, () => {
      openParents.value.forEach((parent) => {
        if (!parent.children?.length) {
          loadChildren(parent).then(() => {
            // preemptively load 1 level below what's open
            if (parent.children) parent.children.forEach(loadChildren)
          });
        }
      })
    });

    watch(activeImage, () => {
      loading.value = false;
      nuclei.value = [];
      showEllipses.value = true;
      selectedElements.value = [];
      initView();
    });

    watch(openPanel, () => {
      if (openPanel.value === 'scatter') {
        nextTick().then(drawScatter)
      }
    });

    watch(selectedElements, () => {
      if (scatterplot.value) {
        // regl-scatterplot requires point indexes
        const selectedIndexes = normalizedPoints.value.map((p, i) => {
          if (selectedElements.value.includes(p.id)) return i
          return undefined
        }).filter((i) => i)
        scatterplot.value.select(selectedIndexes, {preventEvent: true})
      }
      updateEllipses();
    });

    watch(nuclei, () => {
      if (nuclei.value?.length) {
        drawEllipses();
        updateNumVisible();
      }
    });

    watch(showEllipses, updateEllipses);

    watch(featureColor, debounce(updateEllipses, 1000));

    watch(constantColor, () => {
      colorByAttribute.value = undefined;
      colormapType.value = undefined;
      colormapName.value = undefined;
    })

    watch(colorByAttribute, () => {
      colormapType.value = undefined;
      colormapName.value = undefined;
    })

    watch(colormapType, () => {
      colormapName.value = undefined;
    })

    watch(colormapName, updateEllipses)

    watch(currentResult, async () => {
      loadingScatter.value = true;
      if (currentResult.value.contents) {
        await nextTick()  // let canvas element appear
      } else {
        currentResult.value.contents = await fetchResult(currentResult.value);
        availableResults.value = availableResults.value.map((result) => {
          if (result.name === currentResult.value.name) {
            return currentResult.value;
          }
          return result;
        });
      }
      drawScatter();
    })

    return {
      loading,
      loadingScatter,
      treeData,
      openParents,
      activeImage,
      nuclei,
      showEllipses,
      elementList,
      numVisible,
      openPanel,
      featureColor,
      selectedColor,
      constantColor,
      colorByAttribute,
      colormapType,
      colormapName,
      colorbrewer,
      availableResults,
      currentResult,
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
        <v-card
          v-if="loading"
          class="over-map pa-3"
          style="width: fit-content; right: 10px"
        >
          Loading Feature Vector Data...
        </v-card>
        <v-card
          v-if="activeImage && nuclei && nuclei.length"
          class="over-map pa-3"
          style="width: fit-content; right: 10px"
        >
          {{ numVisible }} {{ numVisible !== 1 ? "nuclei" : "nucleus" }} visible
        </v-card>
        <v-btn
          v-if="activeImage"
          icon="mdi-arrow-expand-all"
          class="over-map"
          style="left: 10px"
          @click="resetView"
        ></v-btn>
      </div>
    </v-main>
    <VResizeDrawer v-if="nuclei && nuclei.length" location="right" name="right">
      <v-card-title class="pa-3">Nuclei Options</v-card-title>
      <v-switch
        v-if="nuclei.length"
        v-model="showEllipses"
        label="Show Ellipses"
        class="my-0 px-6"
        hide-details
      />
      <v-expansion-panels
        v-if="nuclei.length"
        v-model="openPanel"
        class="pl-6 pr-3"
        variant="accordion"
      >
        <v-expansion-panel value="elements">
          <v-expansion-panel-title>
            {{ nuclei.length }} nuclei
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
                      <p
                        v-for="detail in Object.entries(element.details)"
                        :key="detail.key"
                      >
                        {{ detail[0] }}: {{ detail[1] }}
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
              v-if="constantColor"
              :color="featureColor"
              size="small"
              class="color-preview"
            />
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-switch v-model="constantColor" label="Constant Color" />
            <v-color-picker
              v-model="featureColor"
              v-if="constantColor"
            ></v-color-picker>
            <v-select
              v-model="colorByAttribute"
              :items="Object.keys(nuclei[0].details)"
              label="Color By Attribute"
              :list-props="{ maxWidth: '300px' }"
            />
            <v-select
              v-model="colormapType"
              v-if="colorByAttribute"
              :items="['sequential', 'singlehue', 'diverging', 'qualitative']"
              label="Colormap Type"
            ></v-select>
            <v-select
              v-model="colormapName"
              v-if="colormapType"
              :items="colorbrewer.schemeGroups[colormapType]"
              label="Colormap Name"
            ></v-select>
          </v-expansion-panel-text>
        </v-expansion-panel>
        <v-expansion-panel
          title="Dimensionality Reduction Results"
          value="scatter"
        >
          <v-expansion-panel-text>
            <v-select
              v-model="currentResult"
              :items="availableResults"
              label="Select Result"
              item-title="name"
              return-object
            />
            <v-table v-if="currentResult" density="compact">
              <tbody>
                <tr
                  v-for="[key, value] in Object.entries(currentResult.metadata)"
                  :key="key"
                >
                  <td>{{ key }}</td>
                  <td>{{ value }}</td>
                </tr>
              </tbody>
            </v-table>
            <div v-if="loadingScatter" class="pa-3 text-center">
              Loading Result Scatterplot...
            </div>
            <canvas v-if="currentResult" id="scatter-canvas"></canvas>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </VResizeDrawer>
  </v-app>
</template>

<style>
.main-area {
  position: absolute;
  top: 65px;
  height: calc(100% - 70px);
  width: 100%;
}
.over-map {
  position: absolute !important;
  z-index: 3 !important;
  top: 10px !important;
}
.color-preview {
  position: absolute;
  top: 10px;
  right: 50px;
}
#scatter-canvas {
  width: 100%;
  height: calc(100vh - 350px);
}
.v-list--slim .v-treeview-group.v-list-group {
  /* decrease tree indent */
  --prepend-width: 5px !important;
}
.v-expansion-panel-text__wrapper {
  padding: 0px 16px !important;
}
</style>
