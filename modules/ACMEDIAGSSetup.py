import shutil
import time

from Const import *
from Util import *

class ACMEDIAGSSetup:
    def __init__(self, conda_setup, env_name):

        workdir = conda_setup.workdir
        env_dir = os.path.join(workdir, 'miniconda', 'envs', env_name)
        if os.path.isdir(env_dir):
            print("Environment {e} is already created.".format(e=env_name))
            self.workdir = conda_setup.workdir
            self.conda_path = conda_setup.conda_path
            self.env = env_name
            return

        self.workdir = conda_setup.workdir
        self.conda_path = conda_setup.conda_path

    def get_env_name(self):
        return self.env

    def create_env_from_yaml_file(self, env_name, env_file_url):

        # get the env yml file
        yml_file_name = "{e}.yml".format(e=env_name)
        env_file = os.path.join(self.workdir, yml_file_name)
        cmd = "wget {url} -O {env_file}".format(url=env_file_url,
                                                env_file=env_file)
        ret_code = run_cmd(cmd, True, False, True)
        if ret_code != SUCCESS:
            print("FAIL...{c}".format(c=cmd))
            return ret_code

        # remove any cached conda packages
        conda_cmd = os.path.join(self.conda_path, 'conda')
        cmd = "{conda} clean --all".format(conda=conda_cmd)

        ret_code = run_cmd(cmd, True, False, True)
        if ret_code != SUCCESS:
            print("FAIL...{c}".format(c=cmd))
            return(ret_code)
        
        # create the environment
        cmd = "{conda} env create -n {env} -f {env_file}".format(conda=conda_cmd,
                                                                 env=env_name,
                                                                 env_file=env_file)
        ret_code = run_cmd(cmd, True, False, True)
        if ret_code != SUCCESS:
            print("FAIL...{c}".format(c=cmd))
            return ret_code

        self.env = env_name

        # conda list for debugging purpose
        cmds_list = ["conda list"]
        ret_code = run_in_conda_env(self.conda_path, env_name, cmds_list)
        if ret_code != SUCCESS:
            print("FAIL...{c}".format(c=cmd))
            return ret_code

    def get_tests(self, build_tests):
        # get test code from 'master' -
        # may need some parameter to determine with
        # version of test to get
        # build_tests - set it to True if we should build the test
        #    i.e. run 'python setup.py install'
        #
        url = "https://github.com/ACME-Climate/acme_diags.git"
        repo_dir = os.path.join(self.workdir, 'acme_diags')

        # check if repo_dir exists already
        if os.path.isdir(repo_dir):
            shutil.rmtree(repo_dir)

        cmd = "git clone {url} {repo_dir}".format(url=url,
                                                  repo_dir=repo_dir)
        ret_code = run_cmd(cmd, True, False, True)
        if ret_code != SUCCESS:
            return ret_code

        # install test code
        if build_tests == True:
            cmds_list = []
            cmds_list.append("cd {repo_dir}".format(repo_dir=repo_dir))
            cmds_list.append("python setup.py install")
        
            ret_code = run_in_conda_env(self.conda_path, self.env, cmds_list)

        return(ret_code)

    def run_system_tests(self, backend=None):
        test_dir = os.path.join(self.workdir, 'acme_diags', 'tests', 'system')
        cmds_list = []
        cmds_list.append("cd {d}".format(d=test_dir))
        if backend:
        cmds_list.append("acme_diags -d all_sets.cfg")
        ret_code = run_in_conda_env(self.conda_path, self.env, cmds_list)

        cmds_list.append(cmd)
        cmd = "echo '================================================================'"
        cmds_list.append(cmd)
        cmds_list.append("cd {d}".format(d=test_dir))
        cmds_list.append("acme_diags -d all_sets.cfg --backend vcs")
        ret_code = run_in_conda_env(self.conda_path, self.env, cmds_list)
        

        return(ret_code)

        
    def run_sets_tests(self, obs_or_model, backend, git_branch):
        """
        obs_or_model: 'model_vs_obs' or 'model_vs_model'
        backend: 'vcs' or 'mpl'
        """
        results_base_dir = "/var/www/acme/acme-diags/e3sm_diags_jenkins"
        results_dir_prefix = "{env}_{backend}_{o_m}".format(env=self.env,
                                                            backend=backend,
                                                            o_m=obs_or_model)
        current_time = time.localtime(time.time())
        time_str = time.strftime("%Y.%m.%d-%H:%M:%S", current_time)

        results_dir = "{base_dir}/{prefix}_{time_stamp}".format(base_dir=results_base_dir,
                                                                prefix=results_dir_prefix,
                                                                time_stamp=time_str)
        print("xxx results_dir: ", results_dir)
        
        test_script = "all_sets_nightly_{o_m}.py".format(o_m=obs_or_model)
        base_url = "https://raw.githubusercontent.com/ACME-Climate/acme_diags"
        workdir = self.workdir
        test_script_url = "{base_url}/{branch}/tests/{test_script}".format(base_url=base_url,
                                                                     branch=git_branch,
                                                                     test_script=test_script)
        test_script_path = "{workdir}/{test_script}".format(workdir=workdir,
                                                            test_script=test_script)
        if os.path.exists(test_script_path):
            os.remove(test_script_path)
        cmd = "wget {url} -O {dest_file}".format(url=test_script_url,
                                                 dest_file=test_script_path)
        ret_code = run_cmd(cmd, True, False, True, workdir)
        if ret_code != SUCCESS:
            return ret_code        
        
        cmds_list = []
        cmd = "acme_diags -p {t} --backend {b} --results_dir {d}".format(t=test_script_path,
                                                                         b=backend,
                                                                         d=results_dir)
        cmds_list.append(cmd)
        ret_code = run_in_conda_env(self.conda_path, self.env, cmds_list)
        return ret_code
                
