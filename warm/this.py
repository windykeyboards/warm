from action import Action

# Class defining the this action
class This(Action):

    def run(self):
        print "This run"

    def __find_src_dir(self):
        # TODO - Find lowest level directory containing .cpp or .h files
        return ""

    def __generate_warm_file(self, name, src_dir):
        pass