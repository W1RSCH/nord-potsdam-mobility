'use strict';

// Browser worker for all-to-all residential-to-employment road assignment.
// A single Dijkstra shortest-path tree is computed per snapped residential zone.
// Destination attraction is accumulated from leaves to origin over tree edges,
// so each OD route contributes to every road segment without rebuilding paths.

function heapPush(nodes, distances, node, distance) {
  let i = nodes.length;
  nodes.push(node);
  distances.push(distance);
  while (i > 0) {
    const parent = (i - 1) >> 1;
    if (distances[parent] <= distance) break;
    nodes[i] = nodes[parent];
    distances[i] = distances[parent];
    i = parent;
  }
  nodes[i] = node;
  distances[i] = distance;
}

function heapPop(nodes, distances) {
  const node = nodes[0];
  const distance = distances[0];
  const lastNode = nodes.pop();
  const lastDistance = distances.pop();
  if (nodes.length) {
    let i = 0;
    while (true) {
      const left = i * 2 + 1;
      const right = left + 1;
      let smallest = i;
      if (left < nodes.length && distances[left] < distances[smallest]) smallest = left;
      if (right < nodes.length && distances[right] < distances[smallest]) smallest = right;
      if (smallest === i) break;
      nodes[i] = nodes[smallest];
      distances[i] = distances[smallest];
      i = smallest;
    }
    nodes[i] = lastNode;
    distances[i] = lastDistance;
  }
  return { node, distance };
}

function runDijkstra(start, nodeCount, offsets, adjTo, adjCost, adjEdge, maxTravel, dist, prevNode, prevEdge, targetMarks, remainingTargets) {
  dist.fill(Infinity);
  prevNode.fill(-1);
  prevEdge.fill(-1);
  const order = [];
  const heapNodes = [];
  const heapDistances = [];
  dist[start] = 0;
  heapPush(heapNodes, heapDistances, start, 0);

  while (heapNodes.length) {
    const item = heapPop(heapNodes, heapDistances);
    const v = item.node;
    const base = item.distance;
    if (base !== dist[v]) continue;
    if (base > maxTravel) break;
    order.push(v);
    if (targetMarks[v]) { targetMarks[v] = 0; remainingTargets--; if (remainingTargets <= 0) break; }
    for (let i = offsets[v]; i < offsets[v + 1]; i++) {
      const next = adjTo[i];
      const cost = base + adjCost[i];
      if (cost <= maxTravel && cost < dist[next]) {
        dist[next] = cost;
        prevNode[next] = v;
        prevEdge[next] = adjEdge[i];
        heapPush(heapNodes, heapDistances, next, cost);
      }
    }
  }
  return { order, remainingTargets };
}

async function calculate(message) {
  const {
    nodeCount, edgeCount, offsets, adjTo, adjCost, adjEdge,
    origins, destinations, targetNodes, maxO, maxD, maxTravel
  } = message;
  if (!nodeCount || !edgeCount || !origins?.length || !destinations?.length) {
    throw new Error('Graph oder Wohn-/Arbeitszugangszonen sind leer.');
  }

  const dist = new Float64Array(nodeCount);
  const prevNode = new Int32Array(nodeCount);
  const prevEdge = new Int32Array(nodeCount);
  const mass = new Float64Array(nodeCount);
  const edgeFlow = new Float64Array(edgeCount);
  const edgeOdCount = new Float64Array(edgeCount);
  const odMass = new Float64Array(nodeCount);
  const targetMarks = new Uint8Array(nodeCount);
  const uniqueTargets = [...new Set(Array.from(targetNodes || []))];
  const maxOrigin = Math.max(Number(maxO) || 1, 1);
  const maxDestination = Math.max(Number(maxD) || 1, 1);
  const originZoneTotal = origins.reduce((sum, o) => sum + (Number(o.zoneCount) || 1), 0);
  const destinationZoneTotal = destinations.reduce((sum, d) => sum + (Number(d.zoneCount) || 1), 0);
  const pairs = originZoneTotal * destinationZoneTotal;
  let reachable = 0;
  const progressEvery = Math.max(1, Math.floor(origins.length / 100));

  for (let oi = 0; oi < origins.length; oi++) {
    const origin = origins[oi];
    for (const node of uniqueTargets) targetMarks[node] = 1;
    const tree = runDijkstra(origin.node, nodeCount, offsets, adjTo, adjCost, adjEdge, maxTravel, dist, prevNode, prevEdge, targetMarks, uniqueTargets.length);
    const order = tree.order;
    // If the origin itself was a destination, the Dijkstra root consumed that target.
    mass.fill(0);
    odMass.fill(0);

    // Add every reachable destination at its snapped road node.
    for (const destination of destinations) {
      if (destination.node === origin.node) continue;
      const travelSeconds = dist[destination.node];
      if (!Number.isFinite(travelSeconds) || travelSeconds > maxTravel) continue;
      const zonePairs = (Number(origin.zoneCount) || 1) * (Number(destination.zoneCount) || 1);
      reachable += zonePairs;
      // A smooth gravity-decay function keeps short trips influential without
      // imposing a hard cut-off between arbitrary travel-time bands.
      const destinationWeight = Math.sqrt(Math.max(0, destination.weight) / maxDestination);
      const travelDecay = 1 / Math.pow(1 + travelSeconds / 1800, 1.18);
      mass[destination.node] += destinationWeight * travelDecay;
      odMass[destination.node] += (Number(destination.zoneCount) || 1);
    }

    // Accumulate destination mass backwards through the shortest-path tree.
    const originWeight = Math.sqrt(Math.max(0, origin.weight) / maxOrigin);
    for (let i = order.length - 1; i >= 0; i--) {
      const node = order[i];
      const demand = mass[node];
      if (!(demand > 0)) continue;
      const edgeId = prevEdge[node];
      const parent = prevNode[node];
      if (edgeId < 0 || parent < 0) continue;
      edgeFlow[edgeId] += originWeight * demand;
      mass[parent] += demand;
      const subtreeDestinations = Math.min(destinationZoneTotal, Math.max(0, odMass[node]));
      const addPairs = (Number(origin.zoneCount) || 1) * subtreeDestinations;
      edgeOdCount[edgeId] = Math.min(pairs, edgeOdCount[edgeId] + addPairs);
      odMass[parent] = Math.min(destinationZoneTotal, odMass[parent] + subtreeDestinations);
    }

    if ((oi + 1) % progressEvery === 0 || oi + 1 === origins.length) {
      self.postMessage({ type: 'progress', done: oi + 1, total: origins.length, reachable, pairs });
      // Yield to the worker event loop so it can report progress regularly.
      await new Promise(resolve => setTimeout(resolve, 0));
    }
  }

  self.postMessage({
    type: 'complete',
    edgeFlows: edgeFlow.buffer,
    edgeOdCounts: edgeOdCount.buffer,
    pairs,
    reachable,
    origins: origins.length,
    destinations: destinations.length,
    maxTravel
  }, [edgeFlow.buffer, edgeOdCount.buffer]);
}

self.onmessage = async event => {
  if (event.data?.type !== 'calculate') return;
  try {
    await calculate(event.data);
  } catch (error) {
    self.postMessage({ type: 'error', message: error?.message || String(error) });
  }
};
