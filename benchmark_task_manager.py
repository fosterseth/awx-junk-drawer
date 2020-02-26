from awx.main.models import Credential, JobTemplate, Job, Project, ProjectUpdate, UnifiedJob, UnifiedJobTemplate, Inventory
from awx.main.models.workflow import WorkflowJobTemplate, WorkflowJobTemplateNode
from task_manager_og import TaskManager as TaskManager0, transaction
from awx.main.scheduler.task_manager import TaskManager as TaskManager1

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

def timeit(func):
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
                time.sleep(.5)
            j.save()

# TaskManager7.start_task = start_task
# TaskManager.start_task = start_task

jt = JobTemplate.objects.filter(name="long_task")[0]
project = Project.objects.filter(name="git_fs")[0]
inv = Inventory.objects.filter(name="laptop")[0]
cred = Credential.objects.filter(name="laptop")[0]


def pu_fail():
    pu = project.create_project_update()
    pu.status = "pending"
    pu.save()
    spawn_bulk_jobs(3)
