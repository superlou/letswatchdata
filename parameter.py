class Parameter:
    def __init__(self, name):
        self.name = name
        self.t_series = []
        self.v_series = []
        self.last_was_same = False

    def update(self, time, value):
        if isinstance(value, bool):
            value = int(value)

        # Don't save identical values
        if len(self.v_series) > 0 and self.v_series[-1] == value:
            if not self.last_was_same:
                # The first time we have an identical value, create a point
                self.t_series.append(time)
                self.v_series.append(value)
            else:
                # Otherwise, simply move the dummy point farther out in time
                self.t_series[-1] = time

            self.last_was_same = True
        else:
            self.t_series.append(time)
            self.v_series.append(value)

            self.last_was_same = False

        # if not self.last_was_same:
        #     self.t_series.append(time)
        #     self.v_series.append(value)

    def points(self):
        return list(zip(self.t_series, self.v_series))


class ParameterDB:
    def __init__(self):
        self.parameters = {}

    def get(self, name):
        return self.parameters[name]

    def create(self, name):
        self.parameters[name] = Parameter(name)
        return self.get(name)

    def save(self, filename):
        with open(filename, 'w') as f:
            f.write('parameter,t,v\n')

            for name, parameter in self.parameters.items():
                for t, v in zip(parameter.t_series, parameter.v_series):
                    f.write('{},{},{}\n'.format(name, t, v))

    def load(filename):
        with open(filename) as f:
            pdb = ParameterDB()

            header = f.readline()
            line = f.readline()
            while line:
                name, t, v = line.split(',')
                if not name in pdb.parameters:
                    pdb.create(name)

                pdb.get(name).update(float(t), float(v))

                line = f.readline()

            return pdb
