#!/usr/bin/env python

# Copyright (c) 2020, Paolo Brasolin <paolo.brasolin@gmail.com>

from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.inventory.helpers import get_group_vars
from ansible.parsing.yaml.objects import AnsibleMapping, AnsibleSequence, AnsibleUnicode

import json
import sys

try:
  inventory = sys.argv[1]
except IndexError:
  print("Please provide the inventory as first argument")
  sys.exit(1)

try:
  output = sys.argv[2]
except IndexError:
  print("Please provide the output file as second argument")
  sys.exit(1)

data_loader = DataLoader()
sources = "environments/production/sncf"

inventory_manager = InventoryManager(loader=data_loader, sources=sources)
variable_manager = VariableManager(loader=data_loader, inventory=inventory_manager)

# pattern = 'foo-*'
# hosts = inventory_manager.list_hosts(pattern)

data = {
    "nodes": [],
    "edges": []
}


files_ids = {}

def makepos(thing):
    file, row, col = thing.ansible_pos
    if not file in files_ids:
        files_ids[file] = len(files_ids)
    return (files_ids[file], row, col)

def serialize(thing):
    if type(thing) in [dict]:
        return ("M", None, [(serialize(key), serialize(thing[key])) for key in thing])
    elif type(thing) in [list]:
        return ("A", None, [serialize(item) for item in thing])
    elif type(thing) in [str]:
        return ("S", None, thing)
    elif type(thing) in [bool]:
        return ("B", None, thing)
    elif type(thing) in [int]:
        return ("I", None, thing)
    elif type(thing) in [float]:
        return ("F", None, thing)
    elif type(thing) in [AnsibleMapping]:
        return ("M", makepos(thing), [(serialize(key), serialize(thing[key])) for key in thing])
    elif type(thing) in [AnsibleSequence]:
        return ("A", makepos(thing), [serialize(item) for item in thing])
    elif type(thing) in [AnsibleUnicode]:
        return ("S", makepos(thing), thing)
    else:
        raise Exception('Serializing unknown type: {}'.format(type(thing)))

node_ids = {}

def node_id(node):
    if not node.name in node_ids:
        node_ids[node.name] = len(node_ids)
    return node_ids[node.name]


def select_direct_parents(groups):
    return [g for g in groups if not any([g in gg.parent_groups for gg in groups if g != gg])]


for host in inventory_manager.hosts.values():
    data["nodes"].append({
        "id": node_id(host),
        "label": host.name,
        "leaf": True,
        "meta": serialize(variable_manager.get_vars(host=host)),
    })

for group in inventory_manager.groups.values():
    data["nodes"].append({
        "id": node_id(group),
        "label": group.name,
        "leaf": False,
        "meta": serialize(get_group_vars([group])),
    })

for host in inventory_manager.hosts.values():
    for parent in select_direct_parents(host.groups):
        data["edges"].append({
            "from": node_id(parent),
            "to": node_id(host),
        })

for group in inventory_manager.groups.values():
    for parent in select_direct_parents(group.parent_groups):
        data["edges"].append({
            "from": node_id(parent),
            "to": node_id(group),
        })

with open(output, "w") as file:
  file.write(json.dumps(data))
