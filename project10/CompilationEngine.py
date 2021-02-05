class CompilationEngine():
    STARTING_TOKENS = {
        'var_dec': ['var'],
        'parameter_list': ['('],
        'subroutine_body': ['{'],
        'expression_list': ['('],
        'expression': ['=', '[', '(']
    }
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
        'expression': [';', ')', ']', ',']
    }
    SUBROUTINE_TOKENS = ["function", "method", "constructor"]
    STATEMENT_TOKENS = ['do', 'let', 'while', 'return', 'if']
    TERMINAL_KEYWORDS = ["boolean", "class", "void", "int"]
    CLASS_VAR_DEC_TOKENS = ["static", "field"]
    UNARY_OPERATORS = ['-', '~']
    TERMINAL_TOKEN_TYPES = ["STRING_CONST", "INT_CONST", "IDENTIFIER", "SYMBOL"]
    OPERATORS = [
        '+',
        '-',
        '*',
        '/',
        '&amp;',
        '|',
        '&lt;',
        '&gt;',
        '='
    ]

    def __init__(self, tokenizer, output_file):
        self.tokenizer = tokenizer
        self.output_file = output_file

    # Compila una clase
    def compile_class(self):
        # lo básico para compilar una clase
        self._write_current_outer_tag(body="class")

        while self.tokenizer.has_more_tokens:
            self.tokenizer.advance()

            if self._terminal_token_type() or self._terminal_keyword():
                self._write_current_terminal_token()
            elif self.tokenizer.current_token in self.CLASS_VAR_DEC_TOKENS:
                self.compile_class_var_dec()
            elif self.tokenizer.current_token in self.SUBROUTINE_TOKENS:
                self.compile_subroutine()

        self._write_current_outer_tag(body="/class")

    def compile_class_var_dec(self):
        self._write_current_outer_tag(body="classVarDec")
        self._write_current_terminal_token()

        while self._not_terminal_token_for('class_var_dec'):
            self.tokenizer.advance()
            self._write_current_terminal_token()

        self._write_current_outer_tag(body="/classVarDec")

    # el encargado de compilar la rutina o función
    def compile_subroutine(self):
        self._write_current_outer_tag(body="subroutineDec")
        self._write_current_terminal_token()

        while self._not_terminal_token_for('subroutine'):
            self.tokenizer.advance()

            if self._starting_token_for('parameter_list'):
                self.compile_parameter_list()
            elif self._starting_token_for('subroutine_body'):
                self.compile_subroutine_body()
            else:
                self._write_current_terminal_token()

        self._write_current_outer_tag(body="/subroutineDec")

    def compile_parameter_list(self):
        # escribe el ( inicial
        self._write_current_terminal_token()
        self._write_current_outer_tag(body="parameterList")

        while self._not_terminal_token_for(position='next', keyword_token='parameter_list'):
            self.tokenizer.advance()
            self._write_current_terminal_token()

        self._write_current_outer_tag(body="/parameterList")
        # avanza hasta cerrar el )
        self.tokenizer.advance()
        self._write_current_terminal_token()

    def compile_subroutine_body(self):

        self._write_current_outer_tag(body="subroutineBody")
        # escribimos la llave inicial {
        self._write_current_terminal_token()

        while self._not_terminal_token_for('subroutine'):
            self.tokenizer.advance()

            if self._starting_token_for('var_dec'):
                self.compile_var_dec()
            elif self._statement_token():
                self.compile_statements()
            else:
                self._write_current_terminal_token()

        # cerramos la llave }
        self._write_current_terminal_token()
        self._write_current_outer_tag(body="/subroutineBody")

    def compile_var_dec(self):

        self._write_current_outer_tag(body="varDec")
        self._write_current_terminal_token()

        while self._not_terminal_token_for('var_dec'):
            self.tokenizer.advance()
            self._write_current_terminal_token()

        self._write_current_outer_tag(body="/varDec")

    def compile_statements(self):

        self._write_current_outer_tag(body="statements")

        while self._not_terminal_token_for('subroutine'):
            if self.tokenizer.current_token == "if":
                self.compile_if()
            elif self.tokenizer.current_token == "do":
                self.compile_do()
            elif self.tokenizer.current_token == "let":
                self.compile_let()
            elif self.tokenizer.current_token == "while":
                self.compile_while()
            elif self.tokenizer.current_token == "return":
                self.compile_return()

            self.tokenizer.advance()

        self._write_current_outer_tag(body="/statements")

    def compile_statement_body(self, not_terminate_func, condition_func, do_something_special_func):
        while not_terminate_func():
            self.tokenizer.advance()

            if condition_func():
                do_something_special_func()
            else:
                self._write_current_terminal_token()

    def compile_do(self):
        self._write_current_outer_tag(body="doStatement")
        self._write_current_terminal_token()

        # experimental
        def do_terminator_func():
            return self._not_terminal_token_for('do')

        def do_condition_func():
            return self._starting_token_for('expression_list')

        def do_do_something_func():
            return self.compile_expression_list()

        self.compile_statement_body(do_terminator_func, do_condition_func, do_do_something_func)

        self._write_current_outer_tag(body="/doStatement")

    def compile_let(self):
        self._write_current_outer_tag(body="letStatement")
        self._write_current_terminal_token()

        while self._not_terminal_token_for('let'):
            self.tokenizer.advance()

            if self._starting_token_for('expression'):
                self.compile_expression()
            else:
                self._write_current_terminal_token()

        self._write_current_outer_tag(body="/letStatement")

    def compile_while(self):
        self._write_current_outer_tag(body="whileStatement")
        # escribe
        self._write_current_terminal_token()

        # avanza hasta el comienzo del (
        self.tokenizer.advance()

        # compila lo que haya dentro de los paréntesis ()
        self.compile_expression()

        while self._not_terminal_token_for('while'):
            self.tokenizer.advance()

            if self._statement_token():
                self.compile_statements()
            else:
                self._write_current_terminal_token()
        # escribe el token del terminal
        self._write_current_terminal_token()

        self._write_current_outer_tag(body="/whileStatement")

    def compile_if(self):
        self._write_current_outer_tag(body="ifStatement")
        # escribe el if
        self._write_current_terminal_token()

        # avanza hasta el comienzo de la expresión
        self.tokenizer.advance()

        # compila la expresión dentro de los paréntesis ()
        self.compile_expression()

        def not_terminate_func():
            return self._not_terminal_token_for('if')

        def condition_func():
            return self._statement_token()

        def do_something_special_func():
            return self.compile_statements()

        self.compile_statement_body(not_terminate_func, condition_func, do_something_special_func)

        # compila el else
        if self.tokenizer.next_token == "else":
            self._write_current_terminal_token()
            self.tokenizer.advance()
            # escribe el else
            self._write_current_terminal_token()
            # lo mismo que arriba
            self.compile_statement_body(
                not_terminate_func,
                condition_func,
                do_something_special_func
            )

        # escribe el token del terminal
        self._write_current_terminal_token()
        self._write_current_outer_tag(body="/ifStatement")

    def compile_expression(self):
        self._write_current_terminal_token()
        self._write_current_outer_tag(body="expression")

        if self._starting_token_for('expression') and self._next_token_is_negative_unary_operator():
            unary_negative_token = True
        else:
            unary_negative_token = False
        self.tokenizer.advance()

        while self._not_terminal_token_for('expression'):
            if self._operator_token() and not unary_negative_token:
                self._write_current_terminal_token()
                self.tokenizer.advance()
            else:
                self.compile_term()

        self._write_current_outer_tag(body="/expression")
        self._write_current_terminal_token()

    def compile_expression_in_expression_list(self):
        self._write_current_outer_tag(body="expression")

        # (
        while self._not_terminal_token_for('expression'):
            if self._operator_token():
                self._write_current_terminal_token()
                self.tokenizer.advance()
            else:
                self.compile_term()
                # termina.

        self._write_current_outer_tag(body="/expression")

    # (expresión (',' expresión)* )?
    def compile_expression_list(self):
        # Escribe (
        self._write_current_terminal_token()
        self._write_current_outer_tag(body="expressionList")

        # se salta el ( inicial
        self.tokenizer.advance()

        while self._not_terminal_token_for('expression_list'):
            self.compile_expression_in_expression_list()
            if self._another_expression_coming():
                self._write_current_terminal_token()
                self.tokenizer.advance()

        self._write_current_outer_tag(body="/expressionList")
        # escribe )
        self._write_current_terminal_token()

    def compile_term(self):
        self._write_current_outer_tag(body="term")

        while self._not_terminal_condition_for_term():
            if self.tokenizer.part_of_subroutine_call():
                self.compile_expression_list()
            elif self._starting_token_for('expression'):
                self.compile_expression()
            elif self.tokenizer.current_token in self.UNARY_OPERATORS:
                self._write_current_terminal_token()

                if self._starting_token_for(keyword_token='expression', position='next'):
                    self.tokenizer.advance()
                    self.compile_term()
                    break
                else:
                    self.tokenizer.advance()
                    # escribe el término interno
                    self._write_current_outer_tag(body="term")
                    self._write_current_terminal_token()
                    self._write_current_outer_tag(body="/term")
            else:
                self._write_current_terminal_token()

            # es decir ., i *
            if self._next_token_is_operation_not_in_expression():
                self.tokenizer.advance()
                break

            self.tokenizer.advance()

        self._write_current_outer_tag(body="/term")

    def compile_return(self):
        self._write_current_outer_tag(body="returnStatement")

        if self._not_terminal_token_for(keyword_token='return', position='next'):
            self.compile_expression()
        else:  # escribe return y ;
            self._write_current_terminal_token()
            self.tokenizer.advance()
            self._write_current_terminal_token()

        self._write_current_outer_tag(body="/returnStatement")

    def _write_current_outer_tag(self, body):
        self.output_file.write("<{}>\n".format(body))

    def _write_current_terminal_token(self):
        # conforme al xml esperado
        if self.tokenizer.current_token_type() == "STRING_CONST":
            tag_name = "stringConstant"
        elif self.tokenizer.current_token_type() == "INT_CONST":
            tag_name = "integerConstant"
        else:
            tag_name = self.tokenizer.current_token_type().lower()

        if self.tokenizer.current_token_type() == "STRING_CONST":
            value = self.tokenizer.current_token.replace("\"", "")
        else:
            value = self.tokenizer.current_token

        self.output_file.write(
            "<{}> {} </{}>\n".format(
                tag_name,
                value,
                tag_name
            )
        )

    def _terminal_token_type(self):
        return self.tokenizer.current_token_type() in self.TERMINAL_TOKEN_TYPES

    def _terminal_keyword(self):
        return self.tokenizer.current_token in self.TERMINAL_KEYWORDS

    def _not_terminal_token_for(self, keyword_token, position='current'):
        if position == 'current':
            return not self.tokenizer.current_token in self.TERMINATING_TOKENS[keyword_token]
        elif position == 'next':
            return not self.tokenizer.next_token in self.TERMINATING_TOKENS[keyword_token]

    def _starting_token_for(self, keyword_token, position='current'):
        if position == 'current':
            return self.tokenizer.current_token in self.STARTING_TOKENS[keyword_token]
        elif position == 'next':
            return self.tokenizer.next_token in self.STARTING_TOKENS[keyword_token]

    def _statement_token(self):
        return self.tokenizer.current_token in self.STATEMENT_TOKENS

    def _operator_token(self, position='current'):
        if position == 'current':
            return self.tokenizer.current_token in self.OPERATORS
        elif position == 'next':
            return self.tokenizer.next_token in self.OPERATORS

    def _next_token_is_negative_unary_operator(self):
        return self.tokenizer.next_token == "-"

    def _another_expression_coming(self):
        return self.tokenizer.current_token == ","

    def _not_terminal_condition_for_term(self):
        # la expresión cubre todas las bases
        return self._not_terminal_token_for('expression')

    def _next_token_is_operation_not_in_expression(self):
        return self._operator_token(position='next') and not self._starting_token_for('expression')
