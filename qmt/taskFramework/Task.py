import dask
from collections import OrderedDict
import json
from TaskMetaclass import TaskMetaclass


# todo base import then factories


class Task(object):
    __metaclass__ = TaskMetaclass
    current_instance_id = 0

    def __init__(self, *args, **kwargs):

        if "name" not in kwargs:
            raise AttributeError("All subclasses of Task must have a 'name' keyword argument")

        self.name = kwargs["name"]
        if "#" not in self.name:
            self.name += "#" + str(Task.current_instance_id)
            Task.current_instance_id += 1

        self.argumentDictionary = kwargs
        self.argumentDictionary.pop("name", None)

        self.sweep_manager = None

        previous_tasks = []
        for kwarg in kwargs.values():
            if isinstance(kwarg,Task):
                previous_tasks += [kwarg]
        self.previous_tasks = previous_tasks
        self.result = None

    def to_dict(self):
        result = OrderedDict()
        result_data = OrderedDict()
        result_data['class'] = self.__class__.__name__
        result_data['argumentDictionary'] = self.dependencies_dict()
        result[self.name] = result_data
        return result

    @staticmethod
    def from_dict(dict_representation):
        taskName, data = dict_representation.items()[0]
        className = data['class']
        target_class = TaskMetaclass.class_registry[className]
        kwargs = {}
        for argName, argValue in data['argumentDictionary'].items():
            if Task.isTaskRepresentation(argValue):
                kwargs[argName] = Task.from_dict(argValue)
            else:
                kwargs[argName] = argValue
        print(target_class)
        return target_class(name=taskName, **kwargs)

    def save(self, file_name):
        with open(file_name, 'w') as jsonFile:
            json.dump(self.to_dict(), jsonFile)

    def dependencies_dict(self):
        result = {}
        for argName, argValue in self.argumentDictionary.items():
            if isinstance(argValue, Task):
                result[argName] = argValue.to_dict()
            else:
                result[argName] = argValue

        return result

    def compile(self):
        raise NotImplementedError("Task is abstract. Method 'compile' is defined only for subclasses of Task.")

    def visualize(self,filename=None):
        return self.compile().visualize(filename=filename)

    def run(self):
        if self.result is None:
            self.compile().compute()
            #self.result = self.result.compute()

    @staticmethod
    def remove_self_argument(init_arguments):
        init_arguments.pop('self', None)
        return init_arguments

    @staticmethod
    def isTaskRepresentation(argValue):
        # check if it has form {name:otherDict}
        hasSingleItem = isinstance(argValue, dict) and len(argValue.items()) == 1
        # check if it has the class to reconstitute the task from
        return hasSingleItem and "class" in argValue.values()[0]
