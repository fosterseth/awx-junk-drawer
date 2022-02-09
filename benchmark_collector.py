from django.db.models.deletion import Collector
from awx.main.signals import disable_activity_stream, disable_computed_fields, pre_save, post_save, pre_delete, post_delete, m2m_changed
import time
from awx.main.utils.deletion import AWXCollector
from django.utils.timezone import now
import datetime
import cProfile

# moved firehose script into utils for easier import
from awx.main.utils.firehose2 import generate_jobs


days_ago = 1
num_jobs = 1000

time_created = now() - datetime.timedelta(days=days_ago)
prof = True

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
        qs = Job.objects.all()
        collector.collect(qs)
        collector.delete()

for s in (pre_save, post_save, pre_delete, post_delete, m2m_changed):
    with s.lock:
        del s.receivers[:]
        s.sender_receivers_cache.clear()

print("AWXCollector")
generate_jobs(num_jobs, time_created)
ac = AWXCollector('default')
if prof:
    cProfile.run("delete_jobs(ac)", filename="AWXCollector.prof")
else:
    delete_jobs(ac)


print("Collector")
generate_jobs(num_jobs, time_created)
oc = Collector('default')
if prof:
    cProfile.run("delete_jobs(oc)", filename="Collector.prof")
else:
    delete_jobs(oc)
