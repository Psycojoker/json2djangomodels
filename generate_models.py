from json import load

models = []


def handle_field(fields, model_name):
    result = []
    for field in fields:
        if field["type"] == "unicode":
            if field["max_len"] <= 255:
                result.append("%s = models.CharField(max_length=255)" % field["name"])
            else:
                result.append("%s = models.TextField()" % field["name"])
            if field["null"]:
                result[-1] = result[-1][:-1] + ", null=True, blank=True)"
        elif field["type"] == "int":
            result.append("%s = models.IntegerField()" % field["name"])
            if field["null"]:
                result[-1] = result[-1][:-1] + ", null=True)"
        elif field["type"] == "bool":
            if field["null"]:
                result.append("%s = models.NullBooleanField()" % field["name"])
            else:
                result.append("%s = models.BooleanField()" % field["name"])
        elif field["type"] == "dict":
            result += map(lambda x: field["name"] + "_" + x, handle_field(field["fields"], model_name))
        elif field["type"] == "list" and field["fields"] == ["string"]:
            models.append({"name": field["key"], "fields": ["%s = models.ForeignKey('%s')" % (model_name.lower().replace(" ", "_"), model_name), "%s = models.CharField(max_length=255)" % field["name"].lower().replace(" ", "_")]})
        elif field["type"] in ("list", "list and dict"):
            models.append({"name": field["key"], "fields": ["%s = models.ForeignKey('%s')" % (model_name.lower().replace(" ", "_"), model_name)] + handle_field(field["fields"], field["key"])})
        else:
            print field["type"]

    return result


if __name__ == "__main__":
    json_data = load(open("parltrack.json", "r"))["fields"]
    model_name = "MEP"
    model = {"name": model_name, "fields": handle_field(json_data, model_name)}

    models = [model] + models

    print "from django.db import models"
    print
    print
    for model in models:
        print "class %s(models.Model):" % model["name"].title().replace(" ", "").replace("_", "")
        for field in sorted(model["fields"]):
            print "    %s" % field
        print
        print

    print "from django.db import transaction"
    print "from json import load"
    print "from models import *"
    print
    print
    print "models_data = load(open('parltrack.json', 'r'))"
    print
    print "with transaction.commit_on_success():"
    print "    for %s in models_data:" % model_name.lower()
    print "        new_%s = %s()" % (model_name.lower(), model_name.title().replace(" ", "").replace("_", ""))
    for field in filter(lambda x: x["type"] in ("unicode", "int", "bool"), json_data):
        print "        new_%s.%s = models_data['%s']" % (model_name.lower(), field["name"], field["key"])
    for field in filter(lambda x: x["type"] in ("dict",), json_data):
        for sub_field in filter(lambda x: x["type"] in ("unicode", "int", "bool"), field["fields"]):
            print "        new_%s.%s = models_data['%s']['%s']" % (model_name.lower(), sub_field["name"], field["key"], sub_field["key"])
    print "        new_%s.save()" % model_name.lower()
