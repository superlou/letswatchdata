class Parameter:
    def __init__(self, name):
        self.name = name
        self.t_series = []
        self.v_series = []

    def update(self, time, value):
        if isinstance(value, bool):
            value = int(value)

        self.t_series.append(time)
        self.v_series.append(value)

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
