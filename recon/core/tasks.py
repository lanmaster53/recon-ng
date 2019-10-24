from recon.core import base
from recon.core.web.db import Tasks
from rq import get_current_job
import traceback

# These tasks exist outside the web directory to avoid loading the entire 
# application (which reloads the framework) on every task execution.

def run_module(workspace, module):

    results = {}
    try:
        # instantiate important objects
        job = get_current_job()
        recon = base.Recon(check=False, analytics=False, marketplace=False)
        recon.start(base.Mode.JOB, workspace=workspace)
        tasks = Tasks(recon)
        # update the task's status
        tasks.update_task(job.get_id(), status=job.get_status())
        # execute the task
        module = recon._loaded_modules.get(module)
        module.run()
    except Exception as e:
        results['error'] = {
            'type': str(type(e)),
            'message': str(e),
            'traceback': traceback.format_exc(),
        }
    results['summary'] = module._summary_counts
    # update the task's status and results
    tasks.update_task(job.get_id(), status='finished', result=results)
    return results
