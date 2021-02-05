class SymbolTable():

    # Representa los símbolos actuales de una clase dada o subrutina del JackCompiler

    def __init__(self):
        self.symbols = []

    def reset(self):
        """
        Inicia el alcance de la subrutina, es decir reseteamos su alcance
        """
        self.symbols = []

    def define(self, name, symbol_type, kind):
        new_symbol = {
            'name': name,
            'type': symbol_type,
            'kind': kind,
            'index': self.var_count(kind)
        }
        self.symbols.append(new_symbol)

    def var_count(self, kind):
        """
        devuelve el número de variables del tipo dado ya definidas en el alcance actual
        """
        return sum(symbol['kind'] == kind for symbol in self.symbols)

    def kind_of(self, name):
        """
        devuelve el tipo de identificador nombrado en el ámbito actual
        (ESTÁTICO, CAMPO, ARG, VAR, NINGUNO)
        """
        return self.find_symbol_by_name(name).get('kind')

    def type_of(self, name):
        """
        devuelve el tipo de identificador nombrado en el ámbito actual
        """
        return self.find_symbol_by_name(name).get('type')

    def index_of(self, name):
        """
        devuelve el índice asignado al identificador nombrado
        """
        return self.find_symbol_by_name(name).get('index')

    def find_symbol_by_name(self, value):
        for symbol in self.symbols:
            if symbol['name'] == value:
                return symbol
