from SymbolTable import SymbolTable
from VMWriter import VMWriter
from LabelCounter import LabelCounter
from Operator import Operator


class CompilationEngine():
    """
    compila un archivo fuente jack desde un tokenizador jack en formato xml en output_file
    """
    SYMBOL_KINDS = {
        'parameter_list': 'argument',
        'var_dec': 'local'
    }
    TOKENS_THAT_NEED_LABELS = ['if', 'while']
    TERMINATING_TOKENS = {
        'class': ['}'],
        'class_var_dec': [';'],
        'subroutine': ['}'],
        'parameter_list': [')'],
        'expression_list': [')'],
        'statements': ['}'],
        'do': [';'],
        'let': [';'],
        'while': ['}'],
        'if': ['}'],
        'var_dec': [';'],
        'return': [';'],
        'expression': [';', ')', ']', ','],
        'array': [']']
    }
    STARTING_TOKENS = {
        'var_dec': ['var'],
        'parameter_list': ['('],
        'subroutine_body': ['{'],
        'expression_list': ['('],
        'expression': ['=', '[', '('],
        'array': ['['],
        'conditional': ['if', 'else']
    }

    def __init__(self, tokenizer, output_file):
        self.tokenizer = tokenizer
        self.output_file = output_file
        self.class_symbol_table = SymbolTable()
        self.subroutine_symbol_table = SymbolTable()
        self.vm_writer = VMWriter(output_file)
        self.label_counter = LabelCounter(labels=self.TOKENS_THAT_NEED_LABELS)
        self.class_name = None

    def compile_class(self):
        """
        lo basico pa compilar la clase
        """
        # omitimos todo para comenzar la clase
        while not self.tokenizer.class_token_reached():
            self.tokenizer.advance()
        # variable de instancia
        self.class_name = self.tokenizer.next_token.text

        while self.tokenizer.has_more_tokens:
            self.tokenizer.advance()

            if self.tokenizer.current_token.starts_class_var_dec():
                self.compile_class_var_dec()
            elif self.tokenizer.current_token.starts_subroutine():
                self.compile_subroutine()

    def compile_class_var_dec(self):
        symbol_kind = self.tokenizer.keyword()

        # obtenemos el tipo del simbolo
        self.tokenizer.advance()
        symbol_type = self.tokenizer.keyword()

        # obtenemos todos los identificadores
        while self._not_terminal_token_for('class_var_dec'):
            self.tokenizer.advance()

            if self.tokenizer.identifier():
                # agregamos los simbolos de clase
                symbol_name = self.tokenizer.identifier()
                self.class_symbol_table.define(
                    name=symbol_name,
                    kind=symbol_kind,
                    symbol_type=symbol_type
                )

    def compile_subroutine(self):
        #  nueva subrutina significa nuevo alcance
        self.subroutine_symbol_table.reset()
        # obtenemos el nombre de la subrutina
        self.tokenizer.advance()
        self.tokenizer.advance()
        subroutine_name = self.tokenizer.current_token.text

        # compilamos la lista de parametros
        self.tokenizer.advance()
        self.compile_parameter_list()

        # compilamos el cuerpo
        self.tokenizer.advance()
        self.compile_subroutine_body(subroutine_name=subroutine_name)

        # reset
        self.label_counter.reset_counts()

    def compile_subroutine_body(self, subroutine_name):
        # saltamos el inicio
        self.tokenizer.advance()
        # obtenemos todas las locales
        num_locals = 0
        while self._starting_token_for('var_dec'):
            num_locals += self.compile_var_dec()
            self.tokenizer.advance()

        # escribimos el comando de funcion
        self.vm_writer.write_function(
            name='{}.{}'.format(self.class_name, subroutine_name),
            num_locals=num_locals
        )

        # compilamos todas las declaraciones
        while self._not_terminal_token_for('subroutine'):
            self.compile_statements()

    def compile_parameter_list(self):
        # tabla de simbolos
        while self._not_terminal_token_for('parameter_list'):
            self.tokenizer.advance()

            if self.tokenizer.next_token.is_identifier():
                symbol_kind = self.SYMBOL_KINDS['parameter_list']
                symbol_type = self.tokenizer.current_token.text
                symbol_name = self.tokenizer.next_token.text
                self.subroutine_symbol_table.define(
                    name=symbol_name,
                    kind=symbol_kind,
                    symbol_type=symbol_type
                )

    def compile_var_dec(self):

        self.tokenizer.advance()

        symbol_type = self.tokenizer.current_token.text

        num_vars = 0

        # obtenemos todas las variables
        while self._not_terminal_token_for('var_dec'):
            self.tokenizer.advance()

            if self.tokenizer.identifier():
                num_vars += 1
                symbol_kind = self.SYMBOL_KINDS['var_dec']
                symbol_name = self.tokenizer.identifier()
                self.subroutine_symbol_table.define(
                    name=symbol_name,
                    kind=symbol_kind,
                    symbol_type=symbol_type
                )
        # return a las variables procesadas
        return num_vars

    def compile_statements(self):

        statement_compile_methods = {
            'if': self.compile_if,
            'do': self.compile_do,
            'let': self.compile_let,
            'while': self.compile_while,
            'return': self.compile_return
        }

        while self._not_terminal_token_for('subroutine'):
            if self.tokenizer.current_token.is_statement_token():
                statement_type = self.tokenizer.current_token.text
                statement_compile_methods[statement_type]()

            self.tokenizer.advance()

    def compile_do(self):

        self.tokenizer.advance()
        caller_name = self.tokenizer.current_token.text
        symbol = self._find_symbol_in_symbol_tables(symbol_name=caller_name)
        self.tokenizer.advance()
        self.tokenizer.advance()
        subroutine_name = self.tokenizer.current_token.text

        if symbol:
            segment = 'local'
            index = symbol['index']
            symbol_type = symbol['type']
            self.vm_writer.write_push(segment=segment, index=index)
        else:  # es decir llamada al os
            symbol_type = caller_name

        subroutine_call_name = symbol_type + '.' + subroutine_name
        # iniciamos la lista de expresion
        self.tokenizer.advance()
        # obtenemos los argumentos en la lista de expresion
        num_args = self.compile_expression_list()
        # method call
        if symbol:
            # llamando al objeto pasado como un argumento implicito
            num_args += 1
        # escribimos la llamada
        self.vm_writer.write_call(name=subroutine_call_name, num_args=num_args)
        self.vm_writer.write_pop(segment='temp', index='0')

    def compile_let(self):

        # obtener símbolo para almacenar evaluación de expresión
        self.tokenizer.advance()
        symbol_name = self.tokenizer.current_token.text
        symbol = self._find_symbol_in_symbol_tables(symbol_name=symbol_name)

        array_assignment = self._starting_token_for(keyword_token='array', position='next')
        if array_assignment:
            # llegar a la expresión de índice
            self.tokenizer.advance()
            self.tokenizer.advance()
            # lo compilamos
            self.compile_expression()
            self.vm_writer.write_push(segment=symbol['kind'], index=symbol['index'])
            self.vm_writer.write_arithmetic(command='+')

        while not self.tokenizer.current_token.text == '=':
            self.tokenizer.advance()
        # compila todas las expresiones
        while self._not_terminal_token_for('let'):
            self.tokenizer.advance()
            self.compile_expression()

        if not array_assignment:
            # almacenar evaluación de expresión en la ubicación del símbolo
            self.vm_writer.write_pop(segment=symbol['kind'], index=symbol['index'])
        else:

            self.vm_writer.write_pop(segment='temp', index='0')

            self.vm_writer.write_pop(segment='pointer', index='1')

            self.vm_writer.write_push(segment='temp', index='0')

            self.vm_writer.write_pop(segment='that', index='0')

    def compile_while(self):

        # escribimos la etiqueta while
        self.vm_writer.write_label(
            label='WHILE_EXP{}'.format(self.label_counter.get('while'))
        )

        # avanzar al inicio (
        self.tokenizer.advance()
        self.tokenizer.advance()

        # compilamos la expresion dentro ()
        self.compile_expression()

        # NOT expresión para manejar fácilmente la terminación y if-goto
        self.vm_writer.write_unary(command='~')
        self.vm_writer.write_ifgoto(
            label='WHILE_END{}'.format(self.label_counter.get('while'))
        )

        while self._not_terminal_token_for('while'):
            self.tokenizer.advance()

            if self._statement_token():
                self.compile_statements()

        # escribir el goto
        self.vm_writer.write_goto(
            label='WHILE_EXP{}'.format(self.label_counter.get('while'))
        )
        # escribimos el fin de la etiqueta
        self.vm_writer.write_label(
            label='WHILE_END{}'.format(self.label_counter.get('while'))
        )
        #  agregar while al contador de etiquetas
        self.label_counter.increment('while')

    def compile_if(self):
        # avanzamos a la expresion start
        self.tokenizer.advance()
        self.tokenizer.advance()
        # compilamos dentro ()
        self.compile_expression()
        self.vm_writer.write_ifgoto(label='IF_TRUE{}'.format(self.label_counter.get('if')))
        self.vm_writer.write_goto(label='IF_FALSE{}'.format(self.label_counter.get('if')))
        self.vm_writer.write_label(label='IF_TRUE{}'.format(self.label_counter.get('if')))
        self.compile_conditional_body()
        if self._starting_token_for(keyword_token='conditional', position='next'):
            self.tokenizer.advance()
            self.vm_writer.write_goto(
                label='IF_END{}'.format(self.label_counter.get('if'))
            )
            self.vm_writer.write_label(
                label='IF_FALSE{}'.format(self.label_counter.get('if'))
            )
            self.compile_conditional_body()
            self.vm_writer.write_label(
                label='IF_END{}'.format(self.label_counter.get('if'))
            )
        else:
            self.vm_writer.write_label(
                label='IF_FALSE{}'.format(self.label_counter.get('if'))
            )

    def compile_conditional_body(self):
        while self._not_terminal_token_for('if'):
            self.tokenizer.advance()

            if self._statement_token():
                if self.tokenizer.current_token.is_if():
                    self.label_counter.increment('if')
                    self.compile_statements()
                    self.label_counter.decrement('if')
                else:
                    self.compile_statements()

    def compile_expression(self):
        """
        many examples..i,e., x = 4
        """
        # las operaciones se compilan al final en orden inverso al que fueron agregadas
        ops = []

        while self._not_terminal_token_for('expression'):
            if self._subroutine_call():
                self.compile_subroutine_call()
            elif self._array_expression():
                self.compile_array_expression()
            elif self.tokenizer.current_token.text.isdigit():
                self.vm_writer.write_push(
                    segment='constant',
                    index=self.tokenizer.current_token.text
                )
            elif self.tokenizer.identifier():
                self.compile_symbol_push()
            elif self.tokenizer.current_token.is_operator() and not self._part_of_expression_list():
                ops.insert(0, Operator(token=self.tokenizer.current_token.text, category='bi'))
            elif self.tokenizer.current_token.is_unary_operator():
                ops.insert(0, Operator(token=self.tokenizer.current_token.text, category='unary'))
            elif self.tokenizer.string_const():
                self.compile_string_const()
            elif self.tokenizer.boolean():  # caso booleano
                self.compile_boolean()
            elif self._starting_token_for('expression'):  # expresión anidada
                # saltamos el inicial (
                self.tokenizer.advance()
                self.compile_expression()
            elif self.tokenizer.null():
                self.vm_writer.write_push(segment='constant', index=0)

            self.tokenizer.advance()

        for op in ops:
            self.compile_op(op)

    def compile_op(self, op):

        if op.unary():
            self.vm_writer.write_unary(command=op.token)
        elif op.multiplication():
            self.vm_writer.write_call(name='Math.multiply', num_args=2)
        elif op.division():
            self.vm_writer.write_call(name='Math.divide', num_args=2)
        else:
            self.vm_writer.write_arithmetic(command=op.token)

    def compile_boolean(self):
        """
        True o False
        """
        self.vm_writer.write_push(segment='constant', index=0)

        if self.tokenizer.boolean() == 'true':
            self.vm_writer.write_unary(command='~')

    def compile_string_const(self):

        string_length = len(self.tokenizer.string_const())
        self.vm_writer.write_push(segment='constant', index=string_length)
        self.vm_writer.write_call(name='String.new', num_args=1)
        # construir cadena a partir de caracteres
        for char in self.tokenizer.string_const():
            if not char == self.tokenizer.STRING_CONST_DELIMITER:
                ascii_value_of_char = ord(char)
                self.vm_writer.write_push(segment='constant', index=ascii_value_of_char)
                self.vm_writer.write_call(name='String.appendChar', num_args=2)

    def compile_symbol_push(self):

        symbol = self._find_symbol_in_symbol_tables(symbol_name=self.tokenizer.identifier())
        segment = symbol['kind']
        index = symbol['index']
        self.vm_writer.write_push(segment=segment, index=index)

    def compile_array_expression(self):

        symbol_name = self.tokenizer.current_token.text
        symbol = self._find_symbol_in_symbol_tables(symbol_name=symbol_name)
        # llegar a la expresión de índice
        self.tokenizer.advance()
        self.tokenizer.advance()
        # compilamos
        self.compile_expression()
        self.vm_writer.write_push(segment='local', index=symbol['index'])
        # agregar dos direcciones: identificador y resultado de expresión
        self.vm_writer.write_arithmetic(command='+')
        self.vm_writer.write_pop(segment='pointer', index=1)
        # agreamos el valor a la pila
        self.vm_writer.write_push(segment='that', index=0)

    def compile_subroutine_call(self):
        """
        example: Memory.peek(8000)
        """
        subroutine_name = ''

        while not self._starting_token_for('expression_list'):
            subroutine_name += self.tokenizer.current_token.text
            self.tokenizer.advance()
        # obtenemos el numero de argumentos
        num_args = self.compile_expression_list()
        # después de enviar argumentos a la pila
        self.vm_writer.write_call(name=subroutine_name, num_args=num_args)

    def compile_expression_list(self):

        num_args = 0

        if self._empty_expression_list():
            return num_args

        # iniciamos las expresiones
        self.tokenizer.advance()

        while self._not_terminal_token_for('expression_list'):
            num_args += 1
            self.compile_expression()
            if self._another_expression_coming():
                self.tokenizer.advance()
        return num_args

    def compile_return(self):
        if self._not_terminal_token_for(keyword_token='return', position='next'):
            self.compile_expression()
        else:
            self.vm_writer.write_push(segment='constant', index='0')
            self.tokenizer.advance()

        self.vm_writer.write_return()

    def _not_terminal_token_for(self, keyword_token, position='current'):
        if position == 'current':
            return not self.tokenizer.current_token.text in self.TERMINATING_TOKENS[keyword_token]
        elif position == 'next':
            return not self.tokenizer.next_token.text in self.TERMINATING_TOKENS[keyword_token]

    def _starting_token_for(self, keyword_token, position='current'):
        if position == 'current':
            return self.tokenizer.current_token.text in self.STARTING_TOKENS[keyword_token]
        elif position == 'next':
            return self.tokenizer.next_token.text in self.STARTING_TOKENS[keyword_token]

    def _statement_token(self):
        return self.tokenizer.current_token.is_statement_token()

    def _another_expression_coming(self):
        return self.tokenizer.current_token.is_expression_list_delimiter()

    def _find_symbol_in_symbol_tables(self, symbol_name):
        if self.subroutine_symbol_table.find_symbol_by_name(symbol_name):
            return self.subroutine_symbol_table.find_symbol_by_name(symbol_name)
        elif self.class_symbol_table.find_symbol_by_name(symbol_name):
            return self.class_symbol_table.find_symbol_by_name(symbol_name)

    def _empty_expression_list(self):
        return self._start_of_expression_list() and self._next_ends_expression_list()

    def _start_of_expression_list(self):
        return self.tokenizer.current_token.text in self.STARTING_TOKENS['expression_list']

    def _next_ends_expression_list(self):
        return self.tokenizer.next_token.text in self.TERMINATING_TOKENS['expression_list']

    def _subroutine_call(self):
        return self.tokenizer.identifier() and self.tokenizer.next_token.is_subroutine_call_delimiter()

    def _array_expression(self):
        return self.tokenizer.identifier() and self._starting_token_for(keyword_token='array', position='next')

    def _part_of_expression_list(self):
        return self.tokenizer.part_of_expression_list()
