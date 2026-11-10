'use strict';

function heapPush(nodes, distances, node, distance) {
  let i = nodes.length;
  nodes.push(node); distances.push(distance);
  while (i > 0) {
    const parent = (i - 1) >> 1;
    if (distances[parent] <= distance) break;
    nodes[i] = nodes[parent]; distances[i] = distances[parent]; i = parent;
  }
  nodes[i] = node; distances[i] = distance;
}
function heapPop(nodes, distances) {
  const node = nodes[0], distance = distances[0];
  const lastNode = nodes.pop(), lastDistance = distances.pop();
  if (nodes.length) {
    let i = 0;
    while (true) {
      const left = i * 2 + 1, right = left + 1; let smallest = i;
      if (left < nodes.length && distances[left] < distances[smallest]) smallest = left;
      if (right < nodes.length && distances[right] < distances[smallest]) smallest = right;
      if (smallest === i) break;
      nodes[i] = nodes[smallest]; distances[i] = distances[smallest]; i = smallest;
    }
    nodes[i] = lastNode; distances[i] = lastDistance;
  }
  return { node, distance };
}

self.onmessage = event => {
  try {
    const {nodeCount, offsets, adjTo, adjCost, sourceNodes, sourceCosts, queryNodes, queryCosts, maxDistance} = event.data;
    if (!nodeCount || !sourceNodes?.length) throw new Error('Keine an das Fußwegenetz angebundenen Haltestellen gefunden.');
    const dist = new Float64Array(nodeCount); dist.fill(Infinity);
    const heapNodes = [], heapDistances = [];
    for (let i = 0; i < sourceNodes.length; i++) {
      const node = sourceNodes[i], cost = sourceCosts[i];
      if (node >= nodeCount || !Number.isFinite(cost)) continue;
      if (cost < dist[node]) { dist[node] = cost; heapPush(heapNodes, heapDistances, node, cost); }
    }
    while (heapNodes.length) {
      const item = heapPop(heapNodes, heapDistances), v = item.node, base = item.distance;
      if (base !== dist[v]) continue;
      if (base > maxDistance) break;
      for (let i = offsets[v]; i < offsets[v + 1]; i++) {
        const next = adjTo[i], cost = base + adjCost[i];
        if (cost <= maxDistance && cost < dist[next]) { dist[next] = cost; heapPush(heapNodes, heapDistances, next, cost); }
      }
    }
    const out = new Float32Array(queryNodes.length);
    for (let i = 0; i < queryNodes.length; i++) {
      const node = queryNodes[i];
      out[i] = node >= 0 && node < nodeCount && Number.isFinite(dist[node]) ? dist[node] + queryCosts[i] : Infinity;
    }
    self.postMessage({type:'complete', distances:out.buffer}, [out.buffer]);
  } catch (error) {
    self.postMessage({type:'error', message:error?.message || String(error)});
  }
};
