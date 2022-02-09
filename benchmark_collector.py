from django.db.models.deletion import Collector
from awx.main.signals import disable_activity_stream, disable_computed_fields
import time
from awx.main.utils.deletion import AWXCollector
from django.utils.timezone import now
import datetime

# moved firehose script into utils for easier import
from awx.main.utils.firehose2 import generate_jobs


days_ago = 1
num_jobs = 1000

time_created = now() - datetime.timedelta(days=days_ago)


def timeit(f):
    def wrapper(*args, **kwargs):
        x = time.time()
        f(*args, **kwargs)
        print()
        print("---->   ", time.time() - x, " seconds")
        print()
    return wrapper

@timeit
def delete_jobs(collector):
    with disable_activity_stream(), disable_computed_fields():
      collector.collect(Job.objects.all())
      collector.delete()

print("AWXCollector")
generate_jobs(num_jobs, time_created)
ac = AWXCollector('default')
delete_jobs(ac)


print("Collector")
generate_jobs(num_jobs, time_created)
oc = Collector('default')
delete_jobs(oc)
