from recon.core import base
from recon.core.web.db import Tasks
from rq import get_current_job
from threading import Lock
import traceback

# These tasks exist outside the web directory to avoid loading the entire 
# application (which reloads the framework) on every task execution.

execution_locks = {}

def run_module_async(workspace, module, options=None):

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
        run_module_with_lock(module, options)

    except Exception as e:
        results['error'] = {
            'type': str(type(e)),
            'message': str(e),
            'traceback': traceback.format_exc(),
        }
    results['summary'] = module._summary_counts
    results['data'] = module._inserted_data
    # update the task's status and results
    tasks.update_task(job.get_id(), status='finished', result=results)
    return results

def run_module_sync(workspace, module_path, options=None):
    recon = base.Recon(check=False, analytics=False, marketplace=False)
    recon.start(base.Mode.JOB, workspace=workspace)
    module = recon._loaded_modules.get(module_path)
    run_module_with_lock(module, options)
    return {
        'summary': module._summary_counts,
        'data': module._inserted_data
    }


def run_module_with_lock(module, options=None):
    if module._modulename not in execution_locks:
        execution_locks[module._modulename] = Lock()

    with execution_locks[module._modulename]:
        if options is not None:
            original_options = module.options.copy()
            module.options.update(options)

        try:
            module.run()
        finally:
            if options is not None:
                module.options.update(original_options)
