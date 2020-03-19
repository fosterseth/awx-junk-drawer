#! /usr/bin/env awx-python

#
# !!! READ BEFORE POINTING THIS AT YOUR FOOT !!!
#
# This script attempts to connect to an AWX database and insert (by default)
# a billion main_jobevent rows as screamingly fast as possible.
#
# tl;dr for best results, feed it high IOPS.
#
# this script exists *solely* for the purpose of generating *test* data very
# quickly; do *not* point this at a production installation or you *will* be
# very unhappy
#
# Before running this script, you should give postgres *GOBS* of memory
# and disk so it can create indexes and constraints as quickly as possible.
# In fact, it's probably not smart to attempt this on anything less than 8 core,
# 32GB of RAM, and tens of thousands of IOPS.
#
# Also, a billion events is a *lot* of data; make sure you've
# provisioned *at least* 750GB of disk space
#
# if you want this script to complete in a few hours, a good starting point
# is something like m5.4xlarge w/ 1TB provisioned IOPS SSD (io1)
#

import argparse
import datetime
import json
import multiprocessing
import pkg_resources
import subprocess
import sys
from io import StringIO
from time import time
from random import randint
from uuid import uuid4

import itertools
import psycopg2

from django import setup as setup_django
from django.db import connection
from django.db.models.sql import InsertQuery
from django.utils.timezone import now


sys.path.insert(0, pkg_resources.get_distribution('awx').module_path)
from awx import prepare_env
prepare_env()
setup_django()

from awx.main.models import UnifiedJob, Job, JobTemplate

db = json.loads(
    subprocess.check_output(
        ['awx-manage', 'print_settings', 'DATABASES', '--format', 'json']
    )
)
name = db['DATABASES']['default']['NAME']
user = db['DATABASES']['default']['USER']
pw = db['DATABASES']['default']['PASSWORD']
host = db['DATABASES']['default']['HOST']

dsn = f'dbname={name} user={user} password={pw} host={host}'

u = str(uuid4())

class YieldedRows(StringIO):

    def __init__(self, job_id_list, rows, *args, **kwargs):
        self.rows = rows * len(job_id_list)
        self.total_rows = self.rows
        self.last_progress = 0
        self.job_id_list = itertools.cycle(job_id_list)
        self.row = "\t".join([
            "2020-01-02 12:00:00",
            "2020-01-02 12:00:01",
            "playbook_on_start",
            "{{}}",
            'false',
            'false',
            "localhost",
            "Example Play",
            "Hello World",
            "",
            "0",
            "1",
            "{0}",
            u,
            "",
            "1",
            "hello_world.yml",
            "0",
            "X",
            "1",
        ]) + '\n'
    def gen_row(self, how_many):
        row = ''
        for _ in range(how_many):
            row += self.row.format(next(self.job_id_list))
        return row
    def read(self, x):
        if self.rows <= 0:
            self.close()
            return ''
        to_gen = int(min(10000, self.rows))
        progress = 100*(self.total_rows - self.rows)/self.total_rows
        if progress - self.last_progress > 10:
            self.last_progress = progress
            print("% complete : {0}".format(progress))
        self.rows -= 10000
        return self.gen_row(to_gen)

# class YieldedRows(StringIO):
#
#     def __init__(self, job_id, rows, *args, **kwargs):
#         self.rows = rows
#         self.row = "\t".join([
#             "2020-01-02 12:00:00",
#             "2020-01-02 12:00:01",
#             "playbook_on_start",
#             "{}",
#             'false',
#             'false',
#             "localhost",
#             "Example Play",
#             "Hello World",
#             "",
#             "0",
#             "1",
#             job_id,
#             u,
#             "",
#             "1",
#             "hello_world.yml",
#             "0",
#             "X",
#             "1",
#         ]) + '\n'
#
#     def read(self, x):
#         if self.rows <= 0:
#             self.close()
#             return ''
#         self.rows -= 10000
#         return self.row * 10000

def firehose(job, count):
    conn = psycopg2.connect(dsn)
    f = YieldedRows(job, count)
    with conn.cursor() as cursor:
        cursor.copy_expert((
            'COPY '
            'main_jobevent('
            'created, modified, event, event_data, failed, changed, '
            'host_name, play, role, task, counter, host_id, job_id, uuid, '
            'parent_uuid, end_line, playbook, start_line, stdout, verbosity'
            ') '
            'FROM STDIN'
        ), f)
    conn.commit()
    conn.close()


def cleanup(sql):
    print(sql)
    conn = psycopg2.connect(dsn)
    with conn.cursor() as cursor:
        cursor.execute(sql)
    conn.commit()
    conn.close()


def generate_jobs(jobs, time_created):
    st = itertools.cycle(['successful', 'failed', 'canceled'])
    print(f'inserting {jobs} job(s)')

    fields = list(set(Job._meta.fields) - set(UnifiedJob._meta.fields))
    job_field_names = set([f.attname for f in fields])
    jt = JobTemplate.objects.first()
    jt_defaults = dict(
        (f.attname, getattr(jt, f.attname))
        for f in JobTemplate._meta.get_fields()
        if f.editable and f.attname in job_field_names and getattr(jt, f.attname)
    )
    jt_defaults['job_template_id'] = jt.pk

    def make_batch(N, **extra):
        jobs = [
            Job(status=next(st), created=time_created, modified=now(), elapsed=0., **extra)
            for i in range(N)
        ]
        ujs = UnifiedJob.objects.bulk_create(jobs)
        query = InsertQuery(Job)
        query.insert_values(fields, ujs)
        with connection.cursor() as cursor:
            query, params = query.sql_with_params()[0]
            cursor.execute(query, params)
        return ujs[-1]

    i = 1
    while jobs > 0:
        s = time()
        print('running batch {}, runtime {}'.format(i, time() - s))
        created = make_batch(min(jobs, 5000), **jt_defaults)
        print('took {}'.format(time() - s))
        i += 1
        jobs -= 5000
    return created


def generate_events(events, job):
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()
    print('removing indexes and constraints')

    # get all the indexes for main_jobevent
    try:
        # disable WAL to drastically increase write speed
        # we're not doing replication, and the goal of this script is to just
        # insert data as quickly as possible without concern for the risk of
        # data loss on crash
        # see: https://www.compose.com/articles/faster-performance-with-unlogged-tables-in-postgresql/
        cursor.execute('ALTER TABLE main_jobevent SET UNLOGGED')

        cursor.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='main_jobevent' AND indexname != 'main_jobevent_pkey';")
        indexes = cursor.fetchall()

        cursor.execute("SELECT conname, contype, pg_catalog.pg_get_constraintdef(r.oid, true) as condef FROM pg_catalog.pg_constraint r WHERE r.conrelid = 'main_jobevent'::regclass AND conname != 'main_jobevent_pkey';")
        constraints = cursor.fetchall()

        # drop all indexes for speed
        for indexname, indexdef in indexes:
            cursor.execute(f'DROP INDEX IF EXISTS {indexname}')
            print(f'DROP INDEX IF EXISTS {indexname}')
        for conname, contype, condef in constraints:
            cursor.execute(f'ALTER TABLE main_jobevent DROP CONSTRAINT IF EXISTS {conname}')
            print(f'ALTER TABLE main_jobevent DROP CONSTRAINT IF EXISTS {conname}')
        conn.commit()

        print(f'attaching {events} events to jobs')
        cores = multiprocessing.cpu_count()
        if events*len(job) < 10000000:
            cores = 1
        workers = []

        for i in range(cores):
            p = multiprocessing.Process(target=firehose, args=(job, events / cores))
            p.daemon = True
            workers.append(p)

        for w in workers:
            w.start()

        for w in workers:
            w.join()

        workers = []

        print('generating unique start/end line counts')
        cursor.execute('CREATE SEQUENCE IF NOT EXISTS firehose_seq;')
        cursor.execute('CREATE SEQUENCE IF NOT EXISTS firehose_line_seq MINVALUE 0;')
        cursor.execute('ALTER SEQUENCE firehose_seq RESTART WITH 1;')
        cursor.execute('ALTER SEQUENCE firehose_line_seq RESTART WITH 0;')
        cursor.execute("SELECT nextval('firehose_line_seq')")
        conn.commit()

        cursor.execute(
            "UPDATE main_jobevent SET "
            "counter=nextval('firehose_seq')::integer,"
            "start_line=nextval('firehose_line_seq')::integer,"
            "end_line=currval('firehose_line_seq')::integer + 2"
        )
        conn.commit()
    finally:
        # restore all indexes
        print(datetime.datetime.utcnow().isoformat())
        print('restoring indexes and constraints (this may take awhile)')

        workers = []
        for indexname, indexdef in indexes:
            p = multiprocessing.Process(target=cleanup, args=(indexdef,))
            p.daemon = True
            workers.append(p)

        for w in workers:
            w.start()

        for w in workers:
            w.join()

        for conname, contype, condef in constraints:
            if contype == 'c':
                # if there are any check constraints, don't add them back
                # (historically, these are > 0 checks, which are basically
                # worthless, because Ansible doesn't emit counters, line
                # numbers, verbosity, etc... < 0)
                continue
            sql = f'ALTER TABLE main_jobevent ADD CONSTRAINT {conname} {condef}'
            cleanup(sql)
    conn.close()
    print(datetime.datetime.utcnow().isoformat())


# def main(jobs, events):
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--jobs', type=int, default=1000000) # 1M by default
    parser.add_argument('--events', type=int, default=1000000000) # 1B by default
    parser.add_argument('--days_ago', type=int, default=0)
    params = parser.parse_args()
    jobs = params.jobs
    events = params.events
    days_ago = params.days_ago
    print(datetime.datetime.utcnow().isoformat())
    time_created = now() - datetime.timedelta(days=days_ago)
    created = generate_jobs(jobs, time_created)
    job_id_list = [j.id for j in Job.objects.all()]
    if events:
        generate_events(events, job_id_list)
    # generate_events(events, str(created.pk))
