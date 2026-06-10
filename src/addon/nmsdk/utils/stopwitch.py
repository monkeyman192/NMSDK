import time
from contextlib import contextmanager
from itertools import accumulate

INDENT = "    "


class StopWitch():
    def __init__(self, auto_nest_sections: bool = True, timer=time.perf_counter):
        self.auto_nest_sections = auto_nest_sections
        self.timer = timer

        self._start_time: float = 0
        self._total_time: float = 0
        # Timing data is always stored raw to avoid any overhead processing it as we add data.
        # This data will be processed later.
        self._timing_data: dict[str, float] = {}
        self._start_times: dict[str, float] = {}
        self._section_name_stack: list[str] = []

    # TODO: Could make a class ala https://stackoverflow.com/a/70059951
    @contextmanager
    def section(self, name: str):
        self.start_section(name)
        yield
        self.end_section(name)

    def start(self):
        self._start_time = self.timer()

    def stop(self):
        stop_time = self.timer()
        # Loop over the items in the start times dict and end all of them.
        for name, start_time in self._start_times.items():
            if name not in self._timing_data:
                self._timing_data[name] = stop_time - start_time
            else:
                self._timing_data[name] += stop_time - start_time
        self._start_times = {}
        # Also set the total time.
        self._total_time += stop_time - self._start_time

    def start_section(self, *args: str):
        start_time = self.timer()
        # For each name in args, start the section. If we are automatically nesting sections, get the parent
        # from the stack and add it.
        if self.auto_nest_sections:
            if len(args) != 1:
                raise ValueError(
                    "Only one section can be created per start_section call when auto section nesting is "
                    "enabled."
                )
            self._section_name_stack.append(args[0])
            self._start_times[".".join(self._section_name_stack)] = start_time
        else:
            # For each name, split it by the . character and then for each sub-component, check to see if it
            # exists in the start times list.
            # This allows us to track the total time of parent groups even if they aren't created explicitly.
            for name in args:
                for subname in list(accumulate(name.split("."), lambda x, y: f"{x}.{y}")):
                    self._start_times[subname] = start_time

    def end_section(self, *args: str):
        end_time = self.timer()
        if self.auto_nest_sections:
            if len(args) != 1:
                raise ValueError(
                    "Only one section can be created per start_section call when auto section nesting is "
                    "enabled."
                )
            name = ".".join(self._section_name_stack)
            start_time = self._start_times.pop(name, self._start_time)
            if name not in self._timing_data:
                self._timing_data[name] = end_time - start_time
            else:
                self._timing_data[name] += end_time - start_time
            self._section_name_stack.pop()
        else:
            # Ending a section will end all sections with the same prefix.
            # If we request a section to be ended which wasn't ever started we just add the name as we have a
            # catch for this later.
            stop_names = set()
            for name in args:
                filtered_names = [x for x in filter(lambda x: x.startswith(name), self._start_times.keys())]
                if filtered_names:
                    stop_names.update(filtered_names)
                else:
                    stop_names.add(name)
            for name in stop_names:
                start_time = self._start_times.pop(name, self._start_time)
                if name not in self._timing_data:
                    self._timing_data[name] = end_time - start_time
                else:
                    self._timing_data[name] += end_time - start_time

    def results(self):
        if self._total_time == 0:
            return
        structured_data = {}
        curr_level = structured_data
        curr_level_name = ""
        # Reformat the data so that it's a set of nested dictionaries, split by the .'s in the names of the
        # sections.
        for name, time_ in self._timing_data.items():
            for part in name.split("."):
                # Generate the current level name.
                if not curr_level_name:
                    curr_level_name = part
                else:
                    curr_level_name += f".{part}"

                # 
                if part not in curr_level:
                    curr_level[part] = {"total_time": -1, "children": {}}
                    if curr_level_name in self._timing_data:
                        curr_level[part]["total_time"] = time_
                elif curr_level_name == name:
                    curr_level[part]["total_time"] = time_
                curr_level = curr_level[part]["children"]
            curr_level = structured_data
            curr_level_name = ""

        def calc_percentage(data: dict, parent_time: float):
            data["percentage"] = f"{100 * data['total_time'] / parent_time:.4f}%"
            for child_data in data["children"].values():
                calc_percentage(child_data, data["total_time"])

        for data in structured_data.values():
            calc_percentage(data, self._total_time)

        def format_data(data: dict, depth: int = 0):
            for key, value in data.items():
                print(f"{INDENT * depth}{key}: {value['total_time']:.4f} ({value['percentage']})")
                if (children := value.get("children")):
                    format_data(children, depth + 1)

        format_data(structured_data)


# Create a "global" object essentially which can be imported from other places.
witch = StopWitch()

if __name__ == "__main__":

    @witch.section("bloop")
    def wait_some():
        time.sleep(0.5)

    witch.start()
    with witch.section("outer"):
        with witch.section("test"):
            time.sleep(2)
        time.sleep(1)
        for i in range(3):
            wait_some()
    witch.stop()
    witch.results()
