class VMWriter():
    # Operadores unarios
    UNARY_OPERATORS = {
        '-': 'neg',
        '~': 'not'
    }
    # Operadores aritméticos lógicos
    ARITHMETIC_LOGICAL_OPERATORS = {
        '+': 'add',
        '-': 'sub',
        '=': 'eq',
        '>': 'gt',
        '<': 'lt',
        '&': 'and',
        '|': 'or'
    }

    def __init__(self, output_file):
        # crea un archivo nuevo archivo con extensión .vm
        self.output_file = output_file

    def write_push(self, segment, index):
        # escribe un comando push vm
        self.output_file.write('push {} {}\n'.format(segment, index))

    def write_pop(self, segment, index):
        """
        escribe un comando pop
        """
        self.output_file.write('pop {} {}\n'.format(segment, index))

    def write_arithmetic(self, command):
        """
        escribe un comando con lógica aritmética
        comandos: ADD, SUB, EQ, GT, LT, AND, OR
        """
        self.output_file.write(
            '{}\n'.format(self.ARITHMETIC_LOGICAL_OPERATORS[command])
        )

    def write_unary(self, command):
        """
        escribe un comando unario
        commands: NEG, NOT
        """
        self.output_file.write(
            '{}\n'.format(self.UNARY_OPERATORS[command])
        )

    def write_label(self, label):
        """
        escribe un comando label
        label: string
        """
        self.output_file.write('label {}\n'.format(label))

    def write_goto(self, label):
        """
        escribe un comando go to vm
        label: string
        """
        self.output_file.write('goto {}\n'.format(label))

    def write_ifgoto(self, label):
        """
        label: string
        """
        self.output_file.write('if-goto {}\n'.format(label))

    def write_call(self, name, num_args):
        """
        escribe un comando de llamada vm
        """
        self.output_file.write(
            'call {} {}\n'.format(name, num_args)
        )

    def write_function(self, name, num_locals):
        """
        escribe un comando de llamada vm
        """
        self.output_file.write('function {} {}\n'.format(name, num_locals))

    def write_return(self):
        """
        escribe un comando return vm
        """
        self.output_file.write('return\n')
