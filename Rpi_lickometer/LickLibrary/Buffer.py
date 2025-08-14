from LickLibrary import Settings, Misc


class Buffer:
    def __init__(self, load=False):
        if load:
            self.data = Misc.pickle_load(Settings.buffer_file)
        else:
            self.data = []

    def save(self):
        Misc.pickle_save(Settings.buffer_file, self.data)
        #todo: also write buffer as human readable text

    def __len__(self):
        return len(self.data)

    def append(self, data):
        #todo: if not data is a list, raise warning
        #todo: raise warning/error is len(data) is not correct
        self.data.append(data)

    def __getitem__(self, item):
        return self.data[item]

    def remove(self, items):
        new_data = [v for i, v in enumerate(self.data) if i not in items]
        self.data = new_data

    def pop(self, item=0):
        return self.data.pop(item)

    @property
    def empty(self):
        if len(self.data) == 0: return True
        return False



# b = Buffer()
# b.append(['999','marx',1.2])

