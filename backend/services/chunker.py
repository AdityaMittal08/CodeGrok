from tree_sitter import Language, Parser
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript

JS_LANGUAGE = Language(tsjavascript.language())
TS_LANGUAGE = Language(tstypescript.language_typescript())
TSX_LANGUAGE = Language(tstypescript.language_tsx())

def get_parser_for_file(file_path: str) -> Parser:
    parser = Parser()
    if file_path.endswith('.tsx'):
        parser.language = TSX_LANGUAGE
    elif file_path.endswith('.ts'):
        parser.language = TS_LANGUAGE
    else:
        parser.language = JS_LANGUAGE
    return parser

def extract_chunks(code: str, file_path: str) -> list[dict]:
    parser = get_parser_for_file(file_path)
    source_bytes = code.encode('utf-8')
    tree = parser.parse(source_bytes)
    chunks = []

    relevant_types = {'function_declaration', 'method_definition', 'arrow_function'}

    def text_for_node(node):
        return source_bytes[node.start_byte:node.end_byte].decode('utf-8')

    def walk(node):
        if node.type in relevant_types:
            name = 'anonymous'
            name_node = node.child_by_field_name('name')
            if name_node:
                name = text_for_node(name_node)
            elif node.parent and node.parent.type == 'variable_declarator':
                var_name_node = node.parent.child_by_field_name('name')
                if var_name_node:
                    name = text_for_node(var_name_node)

            chunks.append({
                'file_path': file_path,
                'function_name': name,
                'ast_type': node.type,
                'start_line': node.start_point[0] + 1,
                'end_line': node.end_point[0] + 1,
                'code_text': text_for_node(node),
            })

        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return chunks