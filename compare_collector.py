from django.db.models.deletion import Collector
from awx.main.management.commands.deletion import AWXCollector, get_candidate_relations_to_delete
from collections import OrderedDict
from django.apps import apps
ac = AWXCollector('default')
oc = Collector('default')

def compare_collector(qs):
    ac = AWXCollector('default')
    oc = Collector('default')
    ac.collect(qs)
    oc.collect(qs)
    ac.sort()
    oc.sort()

    old_del_dict = oc.data

    awx_del_dict = OrderedDict()
    for model, instances in ac.data.items():
        awx_del_dict.setdefault(model, set())
        for inst in instances:
            awx_del_dict[model].update(inst)
    return old_del_dict, awx_del_dict


def print_model_info():
    for m in apps.app_configs['main'].get_models():
        print(m.__name__, " " * max(0, 45-len(m.__name__)), m.objects.count())

def run_compare():
    for m in apps.app_configs['main'].get_models():
        print(m.__name__, m.objects.count())
        try:
            a,b = compare_collector(m.objects.all())
            if a != b:
                print("Does not match!")
            else:
                print("Match!")
        except:
            continue
