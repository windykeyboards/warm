from action import Action

# Class defining the up action
class Up(Action):

    def run(self):
        print("Up run")

    def __diff_to_current(self, dependencies):
        # TODO - Return list of dependencies which need to be fetched
        return []

    def __parse_dependencies(self):
        # TODO - Read and construct data classes defining dependencies
        return []

    def __download_and_apply(self, dependency):
        # TODO - Download given dependency, parse warm file and move files to the right place
        return

    def __output_results(self, depresults):
        print('Done')
    