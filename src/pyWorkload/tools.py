import os,sys,subprocess

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

def run_ibench(num_of_runs, run_name, target_dir):
    dir = "/users/jhe/Home2/tars/artc-0.9b/magritte/"
    cmd = "./runall.sh -n {NUM_RUNS} {RUN_NAME} -c0 {DIRECTORY_TO_REPLAY_IN}".format(
          NUM_RUNS=num_of_runs, 
          RUN_NAME=run_name,
          DIRECTORY_TO_REPLAY_IN=target_dir)
    print cmd
    with cd(dir):
        ret = subprocess.call(cmd.split())
    return ret


#run_ibench(1, "myrun", "/mnt/scratch/")

