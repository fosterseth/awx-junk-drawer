# create blend of data


from django.db.models.deletion import Collector
from awx.main.management.commands.deletion import AWXCollector, get_candidate_relations_to_delete
from collections import OrderedDict
from django.apps import apps
from model_bakery import baker


for m in apps.app_configs['main'].get_models():
    try:
        print(baker.make(m))

    except:
        continue
