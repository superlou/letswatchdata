class Annotator:
    def __init__(self, name, config):
        self.name = name
        self.match_value = config.get('match_value', None)

    def matches(self, param):
        try:
            values = param.v_series
            if values[-1] == self.match_value and values[-2] != self.match_value:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False
