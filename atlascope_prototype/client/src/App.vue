<script lang="js">
import { defineComponent, ref, watch } from "vue";
import { VTreeview } from 'vuetify/labs/VTreeview';
import VResizeDrawer from  '@wdns/vuetify-resize-drawer';
import { listCollections, listFolders, listItems } from "./api";

export default defineComponent({
  components: {
    VTreeview,
    VResizeDrawer,
  },
  setup() {
    const treeData = ref([{
      name: 'Girder Data',
      _id: 'root',
      _modelType: 'root',
      children: []
    }]);
    const activeImage = ref();

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

    watch(activeImage, () => {
      console.log(activeImage.value[0])
    })

    return {
      treeData,
      activeImage,
      loadChildren,
    };
  },
});
</script>

<template>
  <v-app>
    <VResizeDrawer>
      <v-treeview
        v-model:activated="activeImage"
        :items="treeData"
        :load-children="loadChildren"
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
    <v-main>
      <div id="map" style="height: 100%"></div>
    </v-main>
  </v-app>
</template>

<style>
.main-area {
  position: absolute;
  top: 65px;
  height: calc(100% - 70px);
  width: 100%;
}
.v-list--slim .v-treeview-group.v-list-group {
  /* decrease tree indent */
  --prepend-width: 5px !important;
}
</style>
