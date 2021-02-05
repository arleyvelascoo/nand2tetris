from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine
import sys
import os
import glob


class JackCompiler():
    # Genera el archivo de salida en el directorio correspondiente
    @classmethod
    def run(cls, input_file, output_file):
        tokenizer = JackTokenizer(input_file)
        compiler = CompilationEngine(tokenizer, output_file)
        compiler.compile_class()

    @classmethod
    def output_file_for(cls, input_file):
        file_name = os.path.basename(input_file).split(".")[0]
        # generando el nombre del archivo de salida
        return "/".join(input_file.split("/")[:-1]) + "/" + file_name + ".vm"


if __name__ == "__main__" and len(sys.argv) == 2:
    arg = sys.argv[1]
    # Determina sí es un directorio o un archivo,
    # y finalmente elige la ruta destino
    if os.path.isfile(arg):
        files = [arg]
    elif os.path.isdir(arg):
        jack_path = os.path.join(arg, "*.jack")
        files = glob.glob(jack_path)

    # create output directory - MAY NEED TO REMOVE
    for input_file_name in files:
        output_file_name = JackCompiler.output_file_for(input_file_name)
        output_file = open(output_file_name, 'w')
        input_file = open(input_file_name, 'r')
        JackCompiler.run(input_file, output_file)
