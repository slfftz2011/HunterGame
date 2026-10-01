#!/usr/bin/env python3
"""
Minecraft 数据包/资源包打包工具
- 从 defines.yml 读取格式配置
- 分别生成数据包和资源包的 pack.mcmeta
- 支持宏替换 + 命令 JSON 压缩
"""

import os
import sys
import zipfile
import re
import json
import yaml
import argparse
from pathlib import Path

EXTENSIONS = {'.json', '.mcfunction', '.nbt'}
KEEP_FILES = {'README', 'LICENSE'}
IGNORE_DIRS = {'python', '__pycache__', '.git', 'output', "pack.py", "check.py", "report.md", "pack.mcmeta"}
OUTPUT_DIR = 'output'
MACRO_FILE = 'defines.yml'

# 默认格式（Minecraft 1.21.10）
DEFAULT_DATA_MIN_FORMAT = [88, 0]
DEFAULT_DATA_MAX_FORMAT = [88, 33]
DEFAULT_RESOURCE_MIN_FORMAT = [69, 0]
DEFAULT_RESOURCE_MAX_FORMAT = [69, 0]
DEFAULT_DESCRIPTION = "欢迎游玩！"

# ===== 工具函数 =====

def should_ignore(path_parts):
    for part in path_parts:
        if part in IGNORE_DIRS:
            return True
    return False

def compress_json(content):
    try:
        data = json.loads(content)
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    except json.JSONDecodeError:
        return content

def compress_command_json(command):
    """压缩命令中的 JSON 部分"""
    start = -1
    for i, ch in enumerate(command):
        if ch in '[{':
            start = i
            break
    if start == -1:
        return command

    stack = []
    end = start
    for i in range(start, len(command)):
        ch = command[i]
        if ch in '[{':
            stack.append(ch)
        elif ch in ']}':
            if not stack:
                break
            expected = ']' if stack[-1] == '[' else '}'
            if ch == expected:
                stack.pop()
                if not stack:
                    end = i
                    break
    if not stack and end > start:
        json_part = command[start:end+1]
        try:
            data = json.loads(json_part)
            compressed = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            return command[:start] + compressed + command[end+1:]
        except json.JSONDecodeError:
            return command
    return command

def fold_multiline_commands(content):
    """将 .mcfunction 中跨多行的命令折叠为一行"""
    lines = content.splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        keywords = re.compile(r'\b(tellraw|title|bossbar\s+set\s+\S+\s+name)\s+')
        match = keywords.search(stripped)
        if not match:
            result.append(line)
            i += 1
            continue

        open_brackets = stripped.count('[') + stripped.count('{') + stripped.count('(')
        close_brackets = stripped.count(']') + stripped.count('}') + stripped.count(')')

        if open_brackets == close_brackets and not stripped.endswith(('[', '{', '(')):
            result.append(line)
            i += 1
            continue

        merged = line
        j = i + 1
        while j < len(lines) and open_brackets > close_brackets:
            next_line = lines[j].strip()
            if next_line.startswith('#'):
                break
            merged += ' ' + next_line
            open_brackets = merged.count('[') + merged.count('{') + merged.count('(')
            close_brackets = merged.count(']') + merged.count('}') + merged.count(')')
            j += 1

        if open_brackets != close_brackets:
            result.append(merged)
            i = j
            continue

        merged = compress_command_json(merged)
        result.append(merged)
        i = j

    return '\n'.join(result)

def clean_mcfunction(content):
    """删除注释和空行，折叠多行命令"""
    lines = content.splitlines()
    cleaned = [line for line in lines
               if line.strip() and not line.strip().startswith('#')]
    content = '\n'.join(cleaned)
    return fold_multiline_commands(content)

def replace_macros(content, macros):
    if not macros:
        return content
    for key in sorted(macros.keys(), key=len, reverse=True):
        value = macros[key]
        if isinstance(value, list):
            value_str = json.dumps(value, separators=(',', ':'))
        else:
            value_str = str(value)
        pattern = re.escape(f'@{key}@')
        content = re.sub(pattern, value_str, content)
    return content

# ===== 文件收集 =====

def collect_data_files(source_dir, filter_c=False):
    """收集数据包文件（仅 data/ 目录）"""
    source = Path(source_dir).resolve()
    files = []
    for root, dirs, files_list in os.walk(source):
        root_path = Path(root)
        rel_root = root_path.relative_to(source)
        if should_ignore(rel_root.parts):
            continue
        # 只处理 data/ 目录
        if rel_root.parts and rel_root.parts[0] != 'data':
            dirs[:] = []  # 不进入其他目录
            continue
        # filter_c: 跳过 data/c/
        if filter_c and len(rel_root.parts) >= 2 and rel_root.parts[:2] == ('data', 'c'):
            dirs[:] = []
            continue
        for name in files_list:
            file_path = root_path / name
            rel_path = file_path.relative_to(source)
            if should_ignore(rel_path.parts):
                continue
            if filter_c and len(rel_path.parts) >= 2 and rel_path.parts[:2] == ('data', 'c'):
                continue
            if file_path.suffix.lower() in EXTENSIONS:
                files.append(file_path)
    return files

def collect_resource_files(source_dir):
    """收集资源包文件（仅 assets/ 目录）"""
    source = Path(source_dir).resolve()
    files = []
    for root, dirs, files_list in os.walk(source):
        root_path = Path(root)
        rel_root = root_path.relative_to(source)
        if should_ignore(rel_root.parts):
            continue
        # 只处理 assets/ 目录
        if rel_root.parts and rel_root.parts[0] != 'assets':
            dirs[:] = []
            continue
        for name in files_list:
            file_path = root_path / name
            rel_path = file_path.relative_to(source)
            if should_ignore(rel_path.parts):
                continue
            files.append(file_path)
    return files

# ===== pack.mcmeta 生成 =====

def generate_pack_mcmeta(pack_type, macros):
    """
    根据包类型生成 pack.mcmeta 内容。
    pack_type: 'data' 或 'resource'
    """
    if pack_type == 'data':
        min_fmt = macros.get('DATA_MIN_FORMAT', DEFAULT_DATA_MIN_FORMAT)
        max_fmt = macros.get('DATA_MAX_FORMAT', DEFAULT_DATA_MAX_FORMAT)
    else:
        min_fmt = macros.get('RESOURCE_MIN_FORMAT', DEFAULT_RESOURCE_MIN_FORMAT)
        max_fmt = macros.get('RESOURCE_MAX_FORMAT', DEFAULT_RESOURCE_MAX_FORMAT)

    description = macros.get('DESCRIPTION', DEFAULT_DESCRIPTION)

    mcmeta = {
        "pack": {
            "description": description,
            "min_format": min_fmt,
            "max_format": max_fmt
        }
    }
    return json.dumps(mcmeta, ensure_ascii=False, indent=2)

# ===== 打包函数 =====

def pack_data(source_dir, output_zip, macros, filter_c=False):
    """打包数据包"""
    source = Path(source_dir).resolve()
    files = collect_data_files(source, filter_c)

    if not files:
        print("⚠️ 数据包：没有找到任何 data/ 下的文件。")

    output_path = Path(output_zip).parent
    output_path.mkdir(parents=True, exist_ok=True)

    pack_mcmeta = generate_pack_mcmeta('data', macros)

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr('pack.mcmeta', pack_mcmeta)

        for file_path in files:
            arcname = file_path.relative_to(source)
            if file_path.suffix.lower() == '.mcfunction':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = replace_macros(content, macros)
                content = clean_mcfunction(content)
                zipf.writestr(str(arcname), content)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = replace_macros(content, macros)
                content = compress_json(content)
                zipf.writestr(str(arcname), content)
            else:
                zipf.write(file_path, arcname)

    tag = " [无 c 目录]" if filter_c else " [含 c 目录]"
    print(f"✅ 数据包：{output_zip}{tag} (共 {len(files)} 个文件)")

def pack_resource(source_dir, output_zip, macros):
    """打包资源包"""
    source = Path(source_dir).resolve()
    files = collect_resource_files(source)

    if not files:
        print("⚠️ 资源包：没有找到任何 assets/ 下的文件。")

    output_path = Path(output_zip).parent
    output_path.mkdir(parents=True, exist_ok=True)

    pack_mcmeta = generate_pack_mcmeta('resource', macros)

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr('pack.mcmeta', pack_mcmeta)

        for file_path in files:
            arcname = file_path.relative_to(source)
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = replace_macros(content, macros)
                content = compress_json(content)
                zipf.writestr(str(arcname), content)
            else:
                # 二进制文件（.png、.ogg 等）直接写入
                zipf.write(file_path, arcname)

    print(f"✅ 资源包：{output_zip} (共 {len(files)} 个文件)")

# ===== 配置加载 =====

def load_macros(source_dir):
    macro_path = Path(source_dir) / MACRO_FILE
    if not macro_path.exists():
        print(f"警告：未找到 {MACRO_FILE}，将使用默认配置。")
        return {}
    try:
        with open(macro_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        macros = {}
        for k, v in data.items():
            if isinstance(v, (str, int, float)):
                macros[k] = str(v)
            else:
                macros[k] = v  # 保留列表/字典用于格式配置
        return macros
    except Exception as e:
        print(f"错误：读取 {MACRO_FILE} 失败：{e}")
        sys.exit(1)

# ===== 主入口 =====

def main():
    parser = argparse.ArgumentParser(description='打包 Minecraft 数据包/资源包')
    parser.add_argument('--data', action='store_true', help='只打包数据包')
    parser.add_argument('--resource', action='store_true', help='只打包资源包')
    parser.add_argument('--all', action='store_true', help='打包数据包和资源包（默认）')
    parser.add_argument('--version', help='指定版本号（覆盖 defines.yml 中的 VERSION）')
    parser.add_argument('--no-compat', action='store_true', help='不生成兼容版数据包')
    parser.add_argument('--no-generic', action='store_true', help='不生成通用版数据包')
    args = parser.parse_args()

    # 默认打包两者
    if not (args.data or args.resource or args.all):
        args.all = True

    src_dir = '.'
    source = Path(src_dir).resolve()
    macros = load_macros(source)
    version = args.version or macros.get('VERSION', '0.0.0')

    # ===== 数据包 =====
    if args.data or args.all:
        # 通用版（移除 data/c/）
        if not args.no_generic:
            data_generic_zip = Path(OUTPUT_DIR) / f"Age-Data-{version}-generic.zip"
            pack_data(src_dir, str(data_generic_zip), macros, filter_c=True)

        # 兼容版（保留 data/c/）
        if not args.no_compat:
            data_compat_zip = Path(OUTPUT_DIR) / f"Age-Data-{version}-compat.zip"
            pack_data(src_dir, str(data_compat_zip), macros, filter_c=False)

    # ===== 资源包 =====
    if args.resource or args.all:
        resource_zip = Path(OUTPUT_DIR) / f"Age-Assets-{version}.zip"
        pack_resource(src_dir, str(resource_zip), macros)


if __name__ == '__main__':
    main()