import geo from "geojs";

const defaultColor = "#00FF00";

function getFeatureAttribute(label, labels, feature) {
  const index = labels.indexOf(label);
  return feature[index];
}

export function drawEllipses(features, labels, region, layer) {
  const ellipses = features.map((feature) => {
    // add ROI offsets to coords
    let centroidX = getFeatureAttribute(
      "Unconstrained.Identifier.CentroidX",
      labels,
      feature
    );
    let centroidY = getFeatureAttribute(
      "Unconstrained.Identifier.CentroidY",
      labels,
      feature
    );
    let major = getFeatureAttribute("Size.MajorAxisLength", labels, feature);
    let minor = getFeatureAttribute("Size.MinorAxisLength", labels, feature);
    let orientation = getFeatureAttribute(
      "Orientation.Orientation",
      labels,
      feature
    );

    // coordinates are relative to ROI and half resolution
    centroidX *= 2;
    centroidY *= 2;
    centroidX += region.left;
    centroidY += region.top;

    return {
      x: centroidX,
      y: centroidY,
      major,
      minor,
      orientation,
    };
  });
  layer
    .createFeature("marker")
    .style({
      visible: true,
      strokeColor: defaultColor,
      fillOpacity: 0,
      scaleWithZoom: geo.markerFeature.scaleMode.fill,
      rotateWithMap: false,
      symbolValue: (f) => f.minor / f.major,
      rotation: (f) => 0 - f.orientation,
      radius: (f) => f.major / 7,
      // radius: (f) => f.major / layer.map().unitsPerPixel(0),
    })
    .data(ellipses);
  layer.draw();
}

export function drawBoxes(features, labels, region, layer) {
  const boxes = features.map((feature) => {
    let xmin = getFeatureAttribute(
      "Unconstrained.Identifier.Xmin",
      labels,
      feature
    );
    let xmax = getFeatureAttribute(
      "Unconstrained.Identifier.Xmax",
      labels,
      feature
    );
    let ymin = getFeatureAttribute(
      "Unconstrained.Identifier.Ymin",
      labels,
      feature
    );
    let ymax = getFeatureAttribute(
      "Unconstrained.Identifier.Ymax",
      labels,
      feature
    );
    // coordinates are relative to ROI and half resolution
    xmin *= 2;
    xmax *= 2;
    ymin *= 2;
    ymax *= 2;
    xmin += region.left;
    xmax += region.left;
    ymin += region.top;
    ymax += region.top;
    return [
      { x: xmin, y: ymin },
      { x: xmin, y: ymax },
      { x: xmax, y: ymax },
      { x: xmax, y: ymin },
    ];
  });
  layer
    .createFeature("line")
    .data(boxes)
    .style({
      visible: true,
      strokeColor: defaultColor,
      closed: true,
    })
    .draw();
}

export default function drawFeatures(features, layer) {
  if (!features || !features.length || !layer) return;

  // Vector Implementation
  // const feature_rois = Object.groupBy(features, (f) => f.roiname);
  // Object.entries(feature_rois).forEach(([roiname, features]) => {
  //   const region = {};
  //   roiname.split("_").forEach((component) => {
  //     const [key, value] = component.split("-");
  //     if (["top", "bottom", "right", "left"].includes(key)) {
  //       region[key] = parseInt(value);
  //     }
  //   });
  //   const labels = features[0].labels;
  //   // drawEllipses(features, labels, region, layer);
  //   drawBoxes(features, labels, region, layer);
  // });

  // JSON Implementation
  features.forEach((feature_roi) => {
    const roiname = feature_roi.roiname;
    const labels = feature_roi.labels;
    const roi_features = feature_roi.features;
    const region = {};
    roiname.split("_").forEach((component) => {
      const [key, value] = component.split("-");
      if (["top", "bottom", "right", "left"].includes(key)) {
        region[key] = parseInt(value);
      }
    });
    // drawEllipses(roi_features, labels, region, layer);
    drawBoxes(roi_features, labels, region, layer);
  });
}
