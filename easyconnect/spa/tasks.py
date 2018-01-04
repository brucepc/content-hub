# asynchronos scheduled tasks using celery
# for package management user feedback
from __future__ import absolute_import

from djcelery import celery
from time import sleep


@celery.task(bind=True)
def TestTask(self):
    count = 0
    total = 1000
    for count in range(10, total, 1):
        sleep(0.1)
        process_percent = int(100 * float(count) / float(total))
        self.update_state(state='PROGRESS', meta={'process_percent': process_percent})
        print process_percent

    self.update_state(state='COMPLETED', meta={'process_percent': 100})
    return True