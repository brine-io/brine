import json
from collections import OrderedDict

from brine.api import get_dataset_for_info


def info(dataset_name):
    response = get_dataset_for_info(dataset_name)
    ordered = OrderedDict()
    ordered['name'] = response['name']
    ordered['description'] = response['description']
    ordered['versions'] = response['versions']

    print(json.dumps(ordered, indent=4))
