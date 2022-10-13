import addict

v_keys = addict.Dict()

v_keys.v8.name = "nodeType"
v_keys.v8.children = "nodes"


v_keys.v5.name = "name"
v_keys.v5.children = "children"


v_keys.v6 = v_keys.v5
v_keys.v7 = v_keys.v5
v_keys.v4 = v_keys.v5