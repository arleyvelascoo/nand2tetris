class JackTokenizer():
    # símbolos del lenguaje Jack
    SYMBOL_CONVERSIONS = {
        '<': '&lt;',
        '>': '&gt;',
        '\"': '&quot;',
        '&': '&amp;'
    }
    COMMENT_OPERATORS = ["/", "*"]
    KEYWORDS = [
        'class',
        'constructor',
        'function',
        'method',
        'field',
        'static',
        'var',
        'int',
        'char',
        'boolean',
        'void',
        'true',
        'false',
        'null',
        'this',
        'let',
        'do',
        'if',
        'else',
        'while',
        'return'
    ]

    # va a través de archivo .jack y produce una secuencia de tokens
    # ignora los espacios en blanco y comentarios

    def __init__(self, input_file):
        self.input_file = input_file
        self.tokens_found = []
        self.current_token = None
        self.next_token = None
        self.has_more_tokens = True

    # Avanza en la lectura del documento
    def advance(self):
        # Lee el primer carácter
        char = self.input_file.read(1)

        # en este loop salta todos loc comentarios y espacios en blanco
        while char.isspace() or char in self.COMMENT_OPERATORS:
            if char.isspace():
                char = self.input_file.read(1)
            elif char in self.COMMENT_OPERATORS:
                # se asegura de que no haya ningún operador
                last_pos = self.input_file.tell()
                next_2_chars = self.input_file.read(2)
                if not self._is_start_of_comment(char, next_2_chars):
                    # vuelve atrás
                    self.input_file.seek(last_pos)
                    break

                # lee toda la linea
                self.input_file.readline()
                # lee el siguiente carácter
                char = self.input_file.read(1)
            continue

        # encontramos el token
        token = ""

        if self._is_string_const_delimeter(char):
            token += char
            char = self.input_file.read(1)

            while not self._is_string_const_delimeter(char):
                token += char
                char = self.input_file.read(1)
            token += char
        elif char.isalnum():
            while self._is_alnum_or_underscore(char):
                token += char
                last_pos = self.input_file.tell()
                char = self.input_file.read(1)

            # retrocede un carácter que se adelantó
            self.input_file.seek(last_pos)
        else:
            if char in self.SYMBOL_CONVERSIONS:
                token = self.SYMBOL_CONVERSIONS[char]
            else:
                token = char

        # establece los tokens
        if self.current_token:
            self.current_token = self.next_token
            self.next_token = token
            self.tokens_found.append(token)
        else:
            self.current_token = token
            self.next_token = token
            self.tokens_found.append(token)
            # actualiza el siguiente token
            self.advance()

        if not len(self.next_token) > 0:
            self.has_more_tokens = False
            return False
        else:
            return True

    def part_of_subroutine_call(self):
        if len(self.tokens_found) < 3:
            return False

        index = len(self.tokens_found) - 4
        token = self.tokens_found[index]

        if token == ".":
            return True
        else:
            return False

    def current_token_type(self):
        if self.current_token[0] == "\"":
            return "STRING_CONST"
        elif self.current_token in self.KEYWORDS:
            return "KEYWORD"
        elif self.current_token.isnumeric():
            return "INT_CONST"
        elif self.current_token.isalnum():
            return "IDENTIFIER"
        else:
            return "SYMBOL"

    def _is_alnum_or_underscore(self, char):
        return char.isalnum() or char == "_"

    def _is_string_const_delimeter(self, char):
        return char == "\""

    def _is_start_of_comment(self, char, next_2_chars):
        # comentario de forma: // or */
        single_line_comment = next_2_chars[0] == self.COMMENT_OPERATORS[0]
        # comentario de la forma: /**
        multi_line_comment = char == self.COMMENT_OPERATORS[0] and next_2_chars == "**"
        # comentario de la forma:  * comment
        part_of_multi_line_comment = char == self.COMMENT_OPERATORS[1] and next_2_chars[0].isspace() and next_2_chars[
            1] != '('
        return single_line_comment or multi_line_comment or part_of_multi_line_comment
