from action import Action
from collections import namedtuple
import log
import os
from subprocess import check_output, call
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from pathlib import Path
import shutil

@dataclass
class Dependency:
    '''Class for keeping track of a dependency'''
    name: str
    git_url: str 
    version_type: str
    version: str

# Class defining the up action
class Up(Action):

    def run(self):
        log.print_action_header("up")

        # Read all dependencies and validate
        all_deps = self.__parse_dependencies()

        # Check to see which differ
        log.print_subaction_header("Diffing dependencies to current")
        deps_to_sync = self.__diff_to_current(all_deps)

        # Sync dependencies
        results = []

        if len(deps_to_sync) > 0:
            log.print_subaction_header("Syncing {count} dependencies".format(count = len(deps_to_sync)))
            for dependency in deps_to_sync:
                result = self.__download_and_apply(dependency)
                results.append(result)

        # Output results
        log.print_subaction_header("Collating results")
        self.__output_results(results)

    def __diff_to_current(self, dependencies):
        arduino_dir = os.environ["ARDUINO_DIR"]

        if arduino_dir is None:
            log.fatal("No ARDUINO_DIR environment variable set")

        arduino_lib_path = os.path.join(arduino_dir, "libraries")

        current_dir = os.getcwd()

        unsynced_dependencies = []

        for dependency in dependencies:
            # Move to the arduino library directory
            os.chdir(arduino_lib_path)

            dependency_path = Path(os.path.join(os.getcwd(), dependency.name))

            # Short-circuit if the path doesn't exist
            if not dependency_path.exists():
                unsynced_dependencies.append(dependency)
                continue

            # If it's a directory, we need to check the version
            if dependency_path.is_dir():
                # Look for the .warm_dependency - file describing the current revision
                warm_path = os.path.join(str(dependency_path), ".warm_dependency")

                if not Path(warm_path).exists():
                    unsynced_dependencies.append(dependency)
                    continue
                else:
                    # Read in the file to determine revision. This is a data class serialised.
                    # Note the uncautious use of eval here. This file only ever exists on the 
                    # users machine, so if they decide to inject malicious code then it's only 
                    # affecting themselves.
                    with open(warm_path) as warm_properties:
                        current_dep = eval(warm_properties.read().strip())

                        if not current_dep == dependency:
                            unsynced_dependencies.append(dependency)
                            continue

        # Back to where we started
        os.chdir(current_dir)
                
        return unsynced_dependencies

    def __parse_dependencies(self):
        # Look for dependencies.warm in current directory
        log.info("Looking in the current directory for dependencies.warm")

        file_list = [f for f in os.listdir('.') if os.path.isfile(f) and f == 'dependencies.warm'] 
        dep_file = file_list[0] if file_list else None

        if dep_file is None:
            log.fatal("Can't find dependencies.warm in the current directory - is it named properly?")

        log.info("Found dependency file")

        all_deps = []

        current_working_dir = os.getcwd()

        # Use a temporary directory as the outer completion such that we use the same directory for all
        # git repo resolutions
        with TemporaryDirectory() as tempdir:
            with open(dep_file) as f:
                for line_number, line in enumerate(f):
                    # If the line is a comment, skip it
                    if line.strip().startswith('//'):
                        continue

                    # The format of a dependency is as follows:
                    #
                    #                   windykeyboards/butt-in: 1.0
                    # [org or owner name] / [repo name] : [tag | commit hash | branch | plus] 
                    #
                    # The following reads each dependency, detects version type, and constructs a 
                    # named tuple describing the dependency.
                    try:
                        owner = line.strip().split('/')[0]
                        repo_name = line.strip().split('/')[1].split(':')[0].strip()
                        raw_version = line.strip().split(':')[1].strip()
                    except:
                        log.info("Malformed dependency on line {line}".format(line = line_number + 1))
                        continue
                    
                    # In future we can support more than just github. For now, hardcode a git https url
                    git_url = "https://github.com/{owner}/{repo}.git".format(owner = owner, repo = repo_name)

                    parsed_version = self.__parse_version(git_url, raw_version, tempdir)

                    if parsed_version is None:
                        log.info("Malformed version on line {line}").format(line = line_number + 1)
                        continue

                    version_type = parsed_version["type"]
                    version = parsed_version["version"]

                    all_deps.append(Dependency(
                        name = repo_name,
                        git_url = git_url,
                        version_type = version_type,
                        version = version
                    ))
                
        # Change back to the original working directory in case parsing changed the working dir
        os.chdir(current_working_dir)

        log.info("Found {0} dependencies for the current project".format(len(all_deps)))
        return all_deps

    def __parse_version(self, remote_url, raw_version, resolving_dir):
        # If the dependency contains a plus, return the latest version
        if '+' in raw_version:
            return {
                "type": "latest_version",
                "version": "+"
            }

        # Clone a bare copy of the repo, allowing us to scan commits, tags and branches
        git_name = remote_url.split('/')[-1]
        clone_path = os.path.join(resolving_dir, git_name)

        header = "Cloning and parsing dependency for {name}".format(name = git_name.replace('.git', ''))
        log.print_subaction_header(header)

        result = self.__call("git clone --bare {url} {temp_path}".format(url = remote_url, temp_path = clone_path), check_result = False)

        if result is not 0:
            log.warn("No valid repo found at {remote}. Does it look right? Are you connected to the internet?".format(remote = remote_url))
            return None

        # Change to the cloned dir for running the following commands
        os.chdir(clone_path)

        # Clean version
        version = raw_version.strip()

        # Check for commit
        out = self.__call("git rev-list --all").split('\n')
        if version in out:
            return {
                "type": "commit",
                "version": version
            }

        # Check for branch
        out = self.__call("git branch").split('\n')
        if version in out:
            return {
                "type": "branch",
                "version": version
            }

        # Check for tag
        out = self.__call("git tag --list").split('\n')
        if version in out:
            return {
                "type": "tag",
                "version": version
            }

        return None

    def __download_and_apply(self, dependency):
        # TODO - Download given dependency, parse warm file and move files to the right place
        # NOTE - a .warm_dependency file needs to be generated in the root of the library
        starting_dir = os.getcwd()

        with TemporaryDirectory() as tempdir:
            result = self.__call("git clone {remote} {dir}".format(remote = dependency.git_url, dir = tempdir), check_result = False)

            if result is not 0:
                os.chdir(starting_dir)
                return {
                    "success": False,
                    "error": "Git clone failed",
                    "dep_name": dependency.name
                }

            os.chdir(tempdir)

            # Change to the right dependency version
            if not dependency.version_type == "latest_version":
                self.__call("git checkout {hash}".format(hash = dependency.version))

            # Parse .warm_properties file - same format as a java/etc .properties file
            if not Path(".warm_properties").exists():
                os.chdir(starting_dir)
                return {
                    "success": False,
                    "error": "Warm properties file not found - is this repo set up properly?",
                    "dep_name": dependency.name
                }

            # If no src dir property is found, default to the current directory
            src_dir = "/"

            with open(".warm_properties") as f:
                for line in f:
                     # If the line is a comment, skip it
                    if line.strip().startswith('//'):
                        continue
                    
                    line_split = line.strip().split('=')

                    # If the line is incomplete, skip
                    if len(line_split) < 2:
                        continue

                    # Parse the src_dir property
                    if line_split[0] == "SRC_DIR":
                        src_dir = line_split[1]
                        continue

            # Move the src directory to the Arduino libraries path, as well as the generated .warm_dependency file
            arduino_path = os.environ["ARDUINO_DIR"]
            dest_path = os.path.join(arduino_path, "libraries/" + dependency.name)
            src_path = os.path.join(os.getcwd(), src_dir)

            with open(".warm_dependency", "w") as file:
                file.write(str(dependency))

            try:
                # Delete the dest path before moving if it exists
                if Path(dest_path).exists():
                    shutil.rmtree(dest_path)

                # Make the dir
                os.makedirs(dest_path)

                # Move files - For the src files we must do one at a time as otherwise we'd create
                # another SRC_DIR directory within our library
                for f_name in os.listdir(src_path):
                    shutil.move(os.path.join(src_path, f_name), dest_path)

                shutil.move(".warm_dependency", dest_path)
            except OSError as e:
                os.chdir(starting_dir)
                return {
                    "success": False,
                    "error": "Moving failed. Reason: {error}".format(error = e),
                    "dep_name": dependency.name
                }

        os.chdir(starting_dir)

        return {
            "success": True
        }

    def __output_results(self, results):
        successful_results = 0
        failure_results = []

        for result in results:
            if result["success"] is not None and result["success"] is True:
                successful_results = successful_results + 1
                continue
            
            if result["success"] is not None and result["success"] is False:
                failure_results.append({
                    "name": result["dep_name"],
                    "error": result["error"]
                })

        if len(failure_results) == 0 and successful_results == 0:
            log.info("Nothing seems to have happened - all dependencies up to date")
            return
        
        if successful_results > 0:
            log.success("{num_results} dependency updates succeeded".format(num_results = successful_results))

        if len(failure_results) > 0:
            log.info("")
            log.warn("Errors occurred for some dependencies:")
            

        for fail in failure_results:
            log.warn("{name}: {error}".format(name = fail["name"], error = fail["error"]))
            

    def __call(self, command, check_result = True):
        print("")
        log.command(command)
        print("")

        if check_result:
            return check_output(command, shell = True).decode('utf-8')
        else:
            return call(command, shell = True)
