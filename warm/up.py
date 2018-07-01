from action import Action
from collections import namedtuple
import log
import os
from subprocess import check_output, call
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from pathlib import Path

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
        deps_to_sync = self.__diff_to_current(all_deps)

        # Sync dependencies
        for dependency in deps_to_sync:
            self.__download_and_apply(dependency)


    def __diff_to_current(self, dependencies):
        arduino_dir = os.environ["ARDUINO_DIR"]

        if arduino_dir is None:
            log.fatal("No ARDUINO_DIR environment variable set")

        arduino_lib_path = os.join(arduino_dir, "libraries")

        current_dir = os.getcwd()

        unsynced_dependencies = []

        for depedency in dependencies:
            # Move to the arduino library directory
            os.chdir(arduino_lib_path)

            dependency_path = Path(os.join(os.getcwd(), dependency.name))

            # Short-circuit if the path doesn't exist
            if not dependency_path.exists():
                unsynced_dependencies.append(depedency)
                continue

            # If it's a directory, we need to check the version
            if dependency_path.is_dir():
                # Look for the .warm_dependency - file describing the current revision
                warm_path = os.join(str(dependency_path), ".warm_dependency")

                if not Path(warm_path).exists():
                    unsynced_dependencies.append(depedency)
                    continue
                else:
                    # Read in the file to determine revision. This is a data class serialised.
                    # Note the uncautious use of eval here. This file only ever exists on the 
                    # users machine, so if they decide to inject malicious code then it's only 
                    # affecting themselves.
                    with open(warm_path) as warm_properties:
                        current_dep = eval(warm_properties.read())

                        if current_dep is not depedency:
                            unsynced_dependencies.append(depedency)
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
        return

    def __output_results(self, depresults):
        print('Done')

    def __call(self, command, check_result = True):
        print("")
        log.command(command)
        print("")

        if check_result:
            return check_output(command, shell = True).decode('utf-8')
        else:
            return call(command, shell = True)
