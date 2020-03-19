from awx.main.models import Credential, JobTemplate, Job, Project, ProjectUpdate, UnifiedJob, UnifiedJobTemplate, Inventory
from awx.main.models.events import JobEvent
from awx.main.models.workflow import WorkflowJobTemplate, WorkflowJobTemplateNode
from awx.main.scheduler.task_manager import TaskManager as TaskManager1
from django.db import transaction
import datetime, pytz

import time
import cProfile

def spawn_jobs(jt, num_jobs):
    with transaction.atomic():
        for i in range(0, num_jobs):
            job = None
            if type(jt) == JobTemplate:
                job = jt.create_job()
            if type(jt) == Project:
                job =jt.create_project_update()

            job.status="pending"
            job.save()

def cancel_all_jobs(name=None):
    jobs = UnifiedJob.objects.filter(status__in=("running", "pending", "new"))
    for j in jobs:
        if name:
            if name in j.name:
                j.cancel()
        else:
            j.cancel()

def time_it(func):
    t1 = time.time()
    func()
    print(time.time() - t1)

def spawn_jt_proj(jt, num_jobs):
    for i in range(0, num_jobs):
        jt_new = jt.copy_unified_jt()
        proj_new = jt.project.copy_unified_jt()
        jt_new.project = proj_new
        jt_new.save()

def spawn_one_job_per_jt():
    jt = JobTemplate.objects.all()
    for j in jt:
        job = j.create_job()
        job.status="pending"
        job.save()

def delete_copies(name):
    uj = UnifiedJobTemplate.objects.all()
    uj_to_del = list(filter(lambda x: name in x.name, uj))
    print(uj_to_del)
    for u in uj_to_del:
        if u:
            u.delete()

def run_it_baby(func, num=5):
    for i in range(num):
        func()._schedule()

def reset_processed():
    UnifiedJob.objects.filter(status="pending").update(dependencies_processed=False)

def spawn_bulk_jobs(num):
    jobs = []
    for i in range(num):
        j = Job()
        j.job_template = jt
        j.project = project
        j.playbook = jt.playbook
        j.inventory = inv
        j.name = "bulk_{0}".format(i)
        j.status = "canceled"
        j.extra_vars = '{"sleeptime": 60}'
        j.allow_simultaneous = False
        jobs.append(j)
    with transaction.atomic():
        for i,j in enumerate(jobs):
            if i % 100 == 0:
                print(i)
                time.sleep(.5)
            j.save()
            j.credentials.add(cred)

def spawn_workflow(num):
    w = WorkflowJobTemplate()
    w.name = "w1"
    w.save()
    prev_node = None
    for _ in range(num):
        node = WorkflowJobTemplateNode()
        # 10 was a job template I had created previously
        node.unified_job_template_id = 10
        node.workflow_job_template_id = w.id
        node.save()
        if prev_node:
            prev_node.success_nodes.add(node)
            prev_node.save()
        else:
            w.workflow_job_template_nodes.add(node)
            w.save()
        prev_node = node

def spawn_fan(pnode, wid, fan, depth):
    if depth == 0:
        return
    for _ in range(fan):
        node = WorkflowJobTemplateNode()
        node.unified_job_template_id = 10
        node.workflow_job_template_id = wid
        node.save()
        pnode.success_nodes.add(node)
        spawn_fan(node, wid, fan, depth - 1)
    pnode.save()

def spawn_workflow_fan(depth, fan):
    w = WorkflowJobTemplate()
    w.name = "w2"
    w.save()

    node = WorkflowJobTemplateNode()
    node.unified_job_template_id = 10
    node.workflow_job_template_id = w.id
    node.save()

    w.workflow_job_template_nodes.add(node)
    w.save()

    spawn_fan(node, w.id, fan, depth)


def start_task(self, task, rampart_group, dependent_tasks=None, instance=None):
    return

def idkman():
    jobs = Job.objects.filter(status="pending")
    ig = InstanceGroup.objects.first()
    instance = Instance.objects.first()
    for j in jobs:
        k = sum(x.task_impact for x in UnifiedJob.objects.filter(execution_node=instance.hostname,
                                                                    status='pending'))
        j.execution_node = instance.hostname
        j.save()

def spawn_bulk_jobs_simple(num):
    jobs = []
    for _ in range(num):
        j = Job()
        j.job_template = jt
        j.status = "canceled"
        jobs.append(j)
    with transaction.atomic():
        for i,j in enumerate(jobs):
            if i % 100 == 0:
                print(i)
            j.save()

def spawn_job_events(num_per_job):
    jobs = [i.pk for i in Job.objects.all()]
    lenjobs = len(jobs)
    for i,job_id in enumerate(jobs):
        if i % 100 == 0:
            print("{0} / {1}".format(i, lenjobs))
        all_je = []
        for _ in range(num_per_job):
            je = JobEvent()
            je.job_id = job_id
            je.event_data = {'name': 'Hello World Sample',
                'pattern': 'all',
                'play': 'Hello World Sample',
                'play_pattern': 'all',
                'play_uuid': '0242ac12-0005-5466-b36e-000000000006',
                'playbook': 'hello_world.yml',
                'playbook_uuid': '3f80d6ed-9d66-4c29-af58-252d49f677ec',
                'uuid': '0242ac12-0005-5466-b36e-000000000006'}
            je.stdout = '\r\nPLAY [Hello World Sample] ******************************************************'
            all_je.append(je)
        with transaction.atomic():
            for j in all_je:
                j.save()


def create_bulk_job_events(num, save_every_n):
    all_je = []
    job_ids = [j.id for j in Job.objects.all()]
    for i,job_id in enumerate(job_ids):
        if i % 100 == 0:
            print(i)
        for _ in range(num):
            if len(all_je) > save_every_n:
                print('== saving ==')
                JobEvent.objects.bulk_create(all_je)
                all_je = []
            je = JobEvent()
            je.job_id = job_id
            je.event_data = {'name': 'Hello World Sample',
                'pattern': 'all',
                'play': 'Hello World Sample',
                'play_pattern': 'all',
                'play_uuid': '0242ac12-0005-5466-b36e-000000000006',
                'playbook': 'hello_world.yml',
                'playbook_uuid': '3f80d6ed-9d66-4c29-af58-252d49f677ec',
                'uuid': '0242ac12-0005-5466-b36e-000000000006'}
            je.stdout = '\r\nPLAY [Hello World Sample] ******************************************************'
            je.modified = datetime.datetime.now(pytz.utc)
            je.created = datetime.datetime.now(pytz.utc)
            all_je.append(je)
    JobEvent.objects.bulk_create(all_je)

def spawn_je(num_jobs, events_per_job):
    spawn_bulk_jobs_simple(num_jobs)
    create_bulk_job_events(events_per_job, 10000)

# for i in Job._meta.fields:
#     print(i.name)
#     if 'on_delete' in dir(Job._meta.get_field(i.name)):
#         print(Job._meta.get_field(i.name).on_delete)

# TaskManager7.start_task = start_task
# TaskManager.start_task = start_task

jt = JobTemplate.objects.filter(name="Demo Job Template")[0]
project = Project.objects.filter(name="Demo Project")[0]
inv = Inventory.objects.filter(name="Demo Inventory")[0]
cred = Credential.objects.filter(name="Demo Credential")[0]


def pu_fail():
    pu = project.create_project_update()
    pu.status = "pending"
    pu.save()
    spawn_bulk_jobs(3)

def cleanup_jobs():
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'cleanup_jobs', '--days', '0'])

def run_firehose():
    import firehose
    firehose.main()

def delete_prep(qs):
    """Delete the records in the current QuerySet."""
    self._not_support_combined_queries('delete')
    assert not self.query.is_sliced, \
        "Cannot use 'limit' or 'offset' with delete."

    if self._fields is not None:
        raise TypeError("Cannot call delete() after .values() or .values_list()")

    del_query = self._chain()

    # The delete is actually 2 queries - one to find related objects,
    # and one to delete. Make sure that the discovery of related
    # objects is performed on the same database as the deletion.
    del_query._for_write = True

    # Disable non-supported fields.
    del_query.query.select_for_update = False
    del_query.query.select_related = False
    del_query.query.clear_ordering(force_empty=True)

    collector = Collector(using=del_query.db)
    collector.collect(del_query)
    return collector
