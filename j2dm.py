import sys
from operator import add
from json import load, dumps


convert_types = {
    unicode: "string",
    int: "int",
    list: "list",
    dict: "dict",
    bool: "bool",
}


class Field(object):
    def __init__(self, key, total):
        self._items = []
        self.total = total
        self.key = key

    @property
    def items(self):
        self._items =  filter(None, self._items)
        return self._items

    def inc(self, new_item):
        self.items.append(new_item)

    @property
    def type(self):
        field_type = list(set(map(type, self.items)))

        if unicode in field_type and len(field_type) == 1:
            if all(map(lambda x: x.isdigit(), self.items)):
                field_type = "int"
            else:
                field_type = "unicode"
        elif len(field_type) == 1:
            field_type = convert_types[field_type[0]]
        elif all(map(lambda x: x in [list, dict], field_type)):
            field_type = "list and dict"
        elif unicode in field_type and list in field_type and len(field_type) == 2:
            field_type = "unicode and list"
        else:
            raise Exception(field_type)

        return field_type

    def render_sub_field(self):
        if self.type == "dict":
            return map(lambda x: x.render(), handle_list(self.items).values())
        if self.type in ["list", "list and dict"]:
            if self.type == "list and dict":
                sub_fields = reduce(add, map(lambda x: x if type(x) == list else [x], self.items), [])
                if sub_fields is None:
                    sub_fields = []
            else:
                sub_fields = reduce(add, self.items)

            if not sub_fields:
                return []
            if list(set(map(type, sub_fields)))[0] == dict:
                return map(lambda x: x.render(), handle_list(sub_fields).values())
            else:
                return map(lambda x: convert_types.get(x, str(x)), set(map(type, sub_fields)))

    @property
    def frequence(self):
        return str(int(100 * float(len(self.items)) / self.total)) + "%"

    @property
    def null(self):
        return not self.total == len(self.items)

    @property
    def name(self):
        return self.key.lower().replace(" ", "_")

    @property
    def max_len(self):
        return max(map(len, self.items))

    @property
    def min_len(self):
        return min(map(len, self.items))

    def render(self):
        result = {"name": self.name, "key": self.key, "null": self.null, "type": self.type}
        if self.null:
            result["frequence"] = self.frequence
        if self.type == "unicode":
            result["max_len"] = self.max_len
            result["min_len"] = self.min_len
        if self.type in ["dict", "list", "list and dict"]:
            result["fields"] = self.render_sub_field()
        return result


def handle_list(the_list):
    result = {}
    for mep in the_list:
        for key in mep:
            result.setdefault(key, Field(key, len(the_list))).inc(mep[key])
    return result


if __name__ == "__main__":
    #if len(sys.argv) > 1:
        #result = handle_list(load(open(sys.argv[1], "r")))
    #else:
        #result = handle_list(load(sys.stdin))
    result = handle_list(load(open("meps.json", "r")))
    #deputes = load(open("deputes.json", "r"))["deputes"]
    #result = handle_list(map(lambda x: x["depute"], deputes))

    print dumps({"fields": map(lambda x: x.render(), result.values())}, indent=4)
    open("parltrack.json", "w").write(dumps({"fields": map(lambda x: x.render(), result.values())}, indent=4))
