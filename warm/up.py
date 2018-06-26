from action import Action
from collections import namedtuple
import log
import os

# Named tuple defining a dependency 
# TODO - Upgrade to dataclass when moving to Python 3.7
Dependency = namedtuple('Dependency', [
    'name', 
    'git_url', 
    'version_type', 
    'version'])

# Class defining the up action
class Up(Action):

    def run(self):
        log.print_action_header("up")
        all_deps = self.__parse_dependencies()

    def __diff_to_current(self, dependencies):
        # TODO - Return list of dependencies which need to be fetched
        return []

    def __parse_dependencies(self):
        # Look for dependencies.warm in current directory
        log.info("Looking in the current directory for dependencies.warm")

        file_list = [f for f in os.listdir('.') if os.path.isfile(f) and f == 'dependencies.warm'] 
        dep_file = file_list[0] if file_list else None

        if dep_file is None:
            log.fatal("Can't find dependencies.warm in the current directory - is it named properly?")
            quit()

        log.info("Found dependency file")

        all_deps = []
        with open(dep_file) as f:
            for line_number, line in enumerate(f):
                # If the line is a comment, skip it
                if line.strip().startswith('//'):
                    continue

                # The format of a dependency is as follows:
                #
                #                   windykeyboards/butt-in: 1.0
                # [org or owner name] / [repo name] : [tag | commit hash | branch] 
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

                parsed_version = self.__parse_version(raw_version)

                if parsed_version is None:
                    log.info("Malformed version on line {line}").format(line = line_number + 1)
                    continue

                version_type = parsed_version.type
                version = parsed_version.version

                all_deps.append(Dependency(
                    name = repo_name,
                    git_url = git_url,
                    version_type = version_type,
                    version = version
                ))
                

        log.info("Found {0} dependencies for the current project".format(len(all_deps)))
        return all_deps

    def __parse_version(self, raw_version):
        # TODO - Parse raw version into either: 1) Git tag/version; 2) Commit hash 3) Git branch 4) Latest version

        # If the dependency contains a plus, return the latest version
        if '+' in raw_version:
            return {
                "type": "latest_version",
                "version": "+"
            }
        
        # For branch, hash or tag we're going to need to pull the empty repo and look for it


        return {}

    def __parse_stay_file(self):
        # TODO - Read stay file to get locked dependency versions
        return []

    def __download_and_apply(self, dependency):
        # TODO - Download given dependency, parse warm file and move files to the right place
        return

    def __output_results(self, depresults):
        print('Done')
