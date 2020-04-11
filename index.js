// Copyright (c) 2020, Paolo Brasolin <paolo.brasolin@gmail.com>

var container = document.getElementById("mynetwork");
var options = {
  interaction: {
    hover: true,
  },
  nodes: {
    shape: "box",
    labelHighlightBold: false,
    font: {
      face: 'Monospace',
    },
    color: {
      background: "white",
      hover: {
        background: "lightyellow",
        border: "orange"
      },
      highlight: {
        background: "lightyellow",
        border: "red"
      }
    },
  },
  layout: {
      hierarchical: {
        sortMethod: "directed",
        shakeTowards: "leaves",
        levelSeparation: 300,
        direction: "LR",
      }
    },
    edges: {
      smooth: true,
      arrows: { to: true },
      color: {
        color: "black",
        hover: "orange",
        highlight: "red",
      }
    }
};


var data = JSON.parse(document.getElementById('data').innerHTML);

const deserialize = ([type, position, content]) => {
  let result = undefined
  switch(type) {
    case "M": result = new Map(content.map(([k,v])=>[deserialize(k), deserialize(v)])); break;
    case "A": result = new Array(...content.map(deserialize)); break;
    case "S": result = new String(content); break;
    case "B": result = new Boolean(content); break;
    case "I": result = new Number(content); break;
    case "F": result = new Number(content); break;
    default: console.log(type); break;
  }
  result.position = position
  return result
}


const nodesFilter = (node) => {
  const r = document.getElementById('filter').value
  return ([...node.leaves]).some(leaf => (new RegExp(r, "g")).test(leaf))
}


data.nodes.forEach(element => {
  if (element.leaf) element.shape = "ellipse"
  // if (element.leaf) element.level = 0
  // element.level = element.leaf ? 1 : -1
  element.leaves = new Set
  element.vars = deserialize(element.meta)
  if (element.leaf) element.leaves.add(element.label)
});


var leaves = data.nodes.filter(n=>n.leaf)

leaves.forEach(leaf => {
  let tIds = [leaf.id]
  do {
    let sIds = data.edges.filter(e => tIds.includes(e.to)).map(e=>e.from)
    data.nodes.filter(n => sIds.includes(n.id)).forEach(n => { n.leaves.add(leaf.label) })
    tIds = sIds
  } while (tIds.length > 0)
})

const nodes = new vis.DataSet(data.nodes)
const nodesView = new vis.DataView(nodes, { filter: nodesFilter })
var network = new vis.Network(container, { nodes: nodesView, edges: data.edges }, options);

const redraw = () => {
  nodesView.refresh()
  network.fit()
}
document.getElementById('filter').addEventListener('change', redraw)
// document.getElementById('filter').addEventListener('keydown', redraw)
// document.getElementById('filter').addEventListener('keyup', redraw)


network.on('doubleClick', () => network.fit())
network.on('selectNode', (event) => {
  const node = data.nodes.find(n => n.id == event.nodes[0])
  document.getElementById('props').textContent = JSON.stringify(node.meta, null, '  ')
})
network.on('deselectNode', (event) => {
  console.log(event)
  document.getElementById('props').textContent = ""
})

