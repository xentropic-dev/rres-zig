#!/usr/bin/env python3
"""
Generate complete Zig bindings from C headers for rres library.
Auto-generates enum wrappers and function wrappers with automatic enum conversion.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

def to_snake_case(name: str) -> str:
    """Convert C enum name to Zig snake_case."""
    # Remove common prefixes
    name = re.sub(r'^RRES_(DATA_|COMP_|CIPHER_|TEXT_ENCODING_|CODE_LANG_|PIXELFORMAT_|VERTEX_ATTRIBUTE_|VERTEX_FORMAT_|FONT_STYLE_)', '', name)
    name = re.sub(r'^RRES_', '', name)

    result = name.lower()

    # Handle Zig keywords
    if result in ['null', 'undefined', 'error', 'type', 'pub', 'const', 'error']:
        result = result + '_'

    return result

def to_pascal_case(name: str) -> str:
    """Convert rresEnumName to EnumName."""
    if name.startswith('rres'):
        name = name[4:]
    return name

def parse_enum(header_content: str, enum_name: str) -> Optional[Tuple[str, List[Tuple[str, Optional[str]]]]]:
    """Parse a C enum definition and return (zig_name, [(value_name, value), ...])."""
    pattern = rf'typedef enum {enum_name}\s*{{([^}}]+)}}\s*{enum_name};'
    match = re.search(pattern, header_content, re.DOTALL)

    if not match:
        return None

    enum_body = match.group(1)
    values = []

    for line in enum_body.split('\n'):
        value_match = re.match(r'\s*([A-Z_0-9]+)\s*=\s*(\d+)', line)
        if value_match:
            c_name = value_match.group(1)
            c_value = value_match.group(2)
            zig_name = to_snake_case(c_name)
            values.append((zig_name, c_value))
        elif re.match(r'\s*([A-Z_0-9]+)\s*,', line):
            c_name = re.match(r'\s*([A-Z_0-9]+)', line).group(1)
            zig_name = to_snake_case(c_name)
            values.append((zig_name, None))

    if not values:
        return None

    zig_name = to_pascal_case(enum_name)
    return (zig_name, values)

def generate_enum_code(zig_name: str, values: List[Tuple[str, Optional[str]]]) -> str:
    """Generate Zig enum definition."""
    lines = [f"pub const {zig_name} = enum(c_uint) {{"]

    for zig_val, c_val in values:
        if c_val is not None:
            lines.append(f"    {zig_val} = {c_val},")
        else:
            lines.append(f"    {zig_val},")

    lines.append("")
    lines.append("    pub fn toCInt(self: @This()) c_uint {")
    lines.append("        return @intFromEnum(self);")
    lines.append("    }")
    lines.append("")
    lines.append("    pub fn fromCInt(value: c_uint) @This() {")
    lines.append("        return @enumFromInt(value);")
    lines.append("    }")
    lines.append("};")

    return '\n'.join(lines)

def parse_structs(header_content: str) -> List[str]:
    """Parse struct names from C headers."""
    pattern = r'typedef struct (\w+)\s*{'
    matches = re.findall(pattern, header_content)
    return matches

def parse_functions(header_content: str) -> List[Tuple[str, str, str, List[Tuple[str, str]]]]:
    """Parse function signatures. Returns [(name, return_type, raw_signature, [(param_type, param_name), ...]), ...]."""
    # Match RRESAPI function declarations
    pattern = r'RRESAPI\s+([\w\s\*]+?)\s+(\w+)\s*\(([^)]*)\)\s*;'
    matches = re.findall(pattern, header_content)

    functions = []
    for return_type, func_name, params_str in matches:
        return_type = return_type.strip()
        params = []

        if params_str.strip() and params_str.strip() != 'void':
            # Split parameters
            for param in params_str.split(','):
                param = param.strip()
                if not param:
                    continue

                # Parse "type name" - handle pointers
                # Match patterns like "const char *fileName" or "unsigned int rresId"
                param_match = re.match(r'^(.+?)\s+(\**)(\w+)$', param)
                if param_match:
                    param_type = param_match.group(1).strip() + ' ' + param_match.group(2).strip()
                    param_type = param_type.strip()
                    param_name = param_match.group(3)
                    params.append((param_type, param_name))

        functions.append((func_name, return_type, params_str, params))

    return functions

def should_wrap_function(func_name: str, return_type: str, params: List[Tuple[str, str]],
                         c_enum_names: List[str]) -> bool:
    """Determine if a function needs wrapping for enum conversion."""
    # Check if return type is an enum
    if return_type in c_enum_names:
        return True

    # Check if any parameter is an enum
    for param_type, _ in params:
        param_base_type = param_type.replace('const', '').replace('*', '').strip()
        if param_base_type in c_enum_names:
            return True

    return False

def generate_function_wrapper(func_name: str, return_type: str, params: List[Tuple[str, str]],
                               enum_map: Dict[str, str]) -> str:
    """Generate a Zig wrapper function that auto-converts enums."""
    # Build parameter list with Zig enum types
    zig_params = []
    param_conversions = []
    call_params = []

    for param_type, param_name in params:
        param_base_type = param_type.replace('const', '').replace('*', '').strip()

        if param_base_type in enum_map:
            # Use Zig enum type
            zig_enum_name = enum_map[param_base_type]
            zig_params.append(f"{param_name}: {zig_enum_name}")
            param_conversions.append(f"    const c_{param_name} = {param_name}.toCInt();")
            call_params.append(f"c_{param_name}")
        else:
            # Use C type as-is
            zig_params.append(f"{param_name}: {param_type}")
            call_params.append(param_name)

    # Build return type
    return_base_type = return_type.replace('const', '').replace('*', '').strip()
    if return_base_type in enum_map:
        zig_return_type = enum_map[return_base_type]
        needs_return_conversion = True
    else:
        zig_return_type = return_type
        needs_return_conversion = False

    # Generate function
    lines = []
    lines.append(f"pub fn {func_name}({', '.join(zig_params)}) {zig_return_type} {{")

    # Add parameter conversions
    for conversion in param_conversions:
        lines.append(conversion)

    # Call C function
    call_str = f"c.{func_name}({', '.join(call_params)})"

    if needs_return_conversion:
        if zig_return_type != 'void':
            lines.append(f"    const result = {call_str};")
            lines.append(f"    return {zig_return_type}.fromCInt(result);")
        else:
            lines.append(f"    {call_str};")
    else:
        if zig_return_type != 'void':
            lines.append(f"    return {call_str};")
        else:
            lines.append(f"    {call_str};")

    lines.append("}")

    return '\n'.join(lines)

def main():
    # Find the rres.h header
    home = Path.home()
    cache_dir = home / ".cache" / "zig" / "p"

    rres_dirs = sorted(cache_dir.glob("N-V-*"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not rres_dirs:
        print("Error: Could not find rres headers in Zig cache", file=sys.stderr)
        sys.exit(1)

    rres_h = rres_dirs[0] / "src" / "rres.h"
    rres_raylib_h = rres_dirs[0] / "src" / "rres-raylib.h"

    if not rres_h.exists():
        print(f"Error: {rres_h} not found", file=sys.stderr)
        sys.exit(1)

    # Read headers
    header_content = rres_h.read_text()
    if rres_raylib_h.exists():
        header_content += "\n" + rres_raylib_h.read_text()

    # Parse enums
    enum_names = [
        'rresResourceDataType',
        'rresCompressionType',
        'rresEncryptionType',
        'rresErrorType',
        'rresTextEncoding',
        'rresCodeLang',
        'rresPixelFormat',
        'rresVertexAttribute',
        'rresVertexFormat',
        'rresFontStyle',
    ]

    enums = {}
    enum_map = {}  # C name -> Zig name

    for enum_name in enum_names:
        result = parse_enum(header_content, enum_name)
        if result:
            zig_name, values = result
            enums[enum_name] = (zig_name, values)
            enum_map[enum_name] = zig_name

    # Parse structs
    structs = parse_structs(header_content)

    # Parse functions
    functions = parse_functions(header_content)

    # Generate output
    print("//! Zig bindings for rres (raylib resource format)")
    print("//! Auto-generated by scripts/generate_bindings.py")
    print()
    print("const std = @import(\"std\");")
    print("const build_options = @import(\"build_options\");")
    print()
    print("const c = if (build_options.enable_raylib) @cImport({")
    print("    @cInclude(\"raylib.h\");")
    print("    @cInclude(\"rres.h\");")
    print("    @cInclude(\"rres-raylib.h\");")
    print("}) else @cImport({")
    print("    @cInclude(\"rres.h\");")
    print("});")
    print()
    print("pub const rres_raylib = if (build_options.enable_raylib) c else void;")
    print()

    # Generate struct exports
    print("// Types")
    for struct_name in structs:
        print(f"pub const {struct_name} = c.{struct_name};")
    print()

    # Generate enums
    print("// Enums - Type-safe Zig wrappers with automatic conversion")
    for enum_name in enum_names:
        if enum_name in enums:
            zig_name, values = enums[enum_name]
            print(generate_enum_code(zig_name, values))
            print()

    # Generate raw C enum exports for compatibility
    print("// Raw C enums (for direct C interop if needed)")
    for enum_name in enum_names:
        print(f"pub const {enum_name} = c.{enum_name};")
    print()

    # Generate functions
    print("// Functions with automatic enum conversion")
    functions_needing_wrappers = []
    direct_exports = []

    for func_name, return_type, raw_params, params in functions:
        if should_wrap_function(func_name, return_type, params, list(enum_map.keys())):
            functions_needing_wrappers.append((func_name, return_type, params))
        else:
            direct_exports.append(func_name)

    # Generate wrappers
    for func_name, return_type, params in functions_needing_wrappers:
        print(generate_function_wrapper(func_name, return_type, params, enum_map))
        print()

    # Direct exports
    print("// Functions without enum parameters (direct exports)")
    for func_name in direct_exports:
        print(f"pub const {func_name} = c.{func_name};")
    print()

    # Generate helper extensions for structs with enum fields
    print("// Helper extensions for working with enums")
    print()
    print("/// Helper to set compression type on ResourceChunkInfo using Zig enum")
    print("pub fn setCompressionType(info: *rresResourceChunkInfo, comp_type: CompressionType) void {")
    print("    info.compType = @intCast(comp_type.toCInt());")
    print("}")
    print()
    print("/// Helper to get compression type from ResourceChunkInfo as Zig enum")
    print("pub fn getCompressionType(info: rresResourceChunkInfo) CompressionType {")
    print("    return CompressionType.fromCInt(info.compType);")
    print("}")
    print()
    print("/// Helper to set encryption type on ResourceChunkInfo using Zig enum")
    print("pub fn setEncryptionType(info: *rresResourceChunkInfo, cipher_type: EncryptionType) void {")
    print("    info.cipherType = @intCast(cipher_type.toCInt());")
    print("}")
    print()
    print("/// Helper to get encryption type from ResourceChunkInfo as Zig enum")
    print("pub fn getEncryptionType(info: rresResourceChunkInfo) EncryptionType {")
    print("    return EncryptionType.fromCInt(info.cipherType);")
    print("}")
    print()

if __name__ == '__main__':
    main()
