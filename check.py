#!/usr/bin/env python3
"""
综合数据包检查工具（含位置定位）
检查所有引用并报告缺失项的位置
"""

import re
import sys
import json
from pathlib import Path

PACK_ROOT = Path(".")
NAMESPACE = "hg"

FUNCTION_DIR = PACK_ROOT / "data" / NAMESPACE / "function"
TAG_DIR = PACK_ROOT / "data" / NAMESPACE / "tags"
PREDICATE_DIR = PACK_ROOT / "data" / NAMESPACE / "predicate"
ADVANCEMENT_DIR = PACK_ROOT / "data" / NAMESPACE / "advancement"
LOOT_TABLE_DIR = PACK_ROOT / "data" / NAMESPACE / "loot_table"
STRUCTURE_DIR = PACK_ROOT / "data" / NAMESPACE / "structure"

def scan_mcfunction(file_path):
    """扫描单个文件，返回各类引用的 (名称, 行号) 列表"""
    result = {
        'scoreboard_registered': [],  # (name, line)
        'scoreboard_used': [],        # (name, line)
        'tag_refs': {'block': [], 'item': [], 'entity': [], 'function': []},
        'predicate_refs': [],
        'advancement_refs': [],
        'function_calls': [],
        'loot_table_refs': [],
        'structure_refs': [],
    }

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 编译正则
    reg_pattern = re.compile(r'scoreboard\s+objectives\s+add\s+([^\s]+)\s+[^\s]+')
    use_patterns = [
        re.compile(r'scoreboard\s+players\s+add\s+\S+\s+([^\s]+)'),
        re.compile(r'scoreboard\s+players\s+remove\s+\S+\s+([^\s]+)'),
        re.compile(r'scoreboard\s+players\s+set\s+\S+\s+([^\s]+)'),
        re.compile(r'scoreboard\s+players\s+operation\s+\S+\s+([^\s]+)\s+[+\-*/%=&><^]+?\s+\S+\s+([^\s]+)'),
        re.compile(r'scoreboard\s+players\s+get\s+\S+\s+([^\s]+)'),
        re.compile(r'scoreboard\s+players\s+reset\s+\S+\s+([^\s]+)'),
        re.compile(r'scoreboard\s+players\s+enable\s+\S+\s+([^\s]+)'),
        re.compile(r'scoreboard\s+players\s+display\s+\S+\s+([^\s]+)'),
        re.compile(r'scoreboard\s+players\s+\w+\s+\S+\s+([^\s]+)'),
        re.compile(r'execute\s+store\s+(?:result|success)\s+score\s+\S+\s+([^\s]+)'),
        re.compile(r'(?:if|unless)\s+score\s+\S+\s+([^\s]+)\s+[+\-*/%=&><^]+?\s+\S+\s+([^\s]+)'),
        re.compile(r'(?:if|unless)\s+score\s+\S+\s+([^\s]+)\s+matches\s+[^\s]+'),
        re.compile(r'score\s+\S+\s+([^\s]+)'),  # 兜底
    ]

    tag_pattern = re.compile(r'#age:([a-zA-Z0-9_/]+)')
    pred_pattern = re.compile(r'predicate\s+age:([a-zA-Z0-9_/]+)')
    adv_pattern = re.compile(r'advancement\s+(grant|revoke)\s+\S+\s+(?:only\s+)?age:([a-zA-Z0-9_/]+)')
    func_pattern = re.compile(r'function\s+age:([a-zA-Z0-9_/]+)')
    loot_pattern = re.compile(r'loot\s+(give|replace|spawn)\s+.*?age:([a-zA-Z0-9_/]+)')
    struct_pattern = re.compile(r'structure\s+(load|place)\s+age:([a-zA-Z0-9_/]+)')

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if any(kw in stripped for kw in ('tellraw', 'actionbar')):
            continue
        # 记分板注册
        for m in reg_pattern.finditer(line):
            result['scoreboard_registered'].append((m.group(1), line_no))

        # 记分板使用
        for pat in use_patterns:
            matches = pat.findall(line)
            for match in matches:
                if isinstance(match, tuple):
                    for m in match:
                        if m and not m.startswith('#'):
                            result['scoreboard_used'].append((m, line_no))
                else:
                    if match and not match.startswith('#'):
                        result['scoreboard_used'].append((match, line_no))

        # 标签
        for m in tag_pattern.finditer(line):
            tag_path = m.group(1)
            context = line.lower()
            if 'block' in context or 'setblock' in context or 'fill' in context:
                result['tag_refs']['block'].append((tag_path, line_no))
            elif ('items' in context or 'item' in context or 'clear' in context or
                  'container' in context or 'inventory' in context or
                  'give' in context or 'replaceitem' in context or 'loot' in context):
                result['tag_refs']['item'].append((tag_path, line_no))
            elif 'entity' in context or 'tag' in context or 'type' in context or 'summon' in context:
                result['tag_refs']['entity'].append((tag_path, line_no))
            else:
                result['tag_refs']['function'].append((tag_path, line_no))

        # 谓词
        for m in pred_pattern.finditer(line):
            result['predicate_refs'].append((m.group(1), line_no))

        # 进度
        for m in adv_pattern.finditer(line):
            result['advancement_refs'].append((m.group(2), line_no))

        # 函数
        for m in func_pattern.finditer(line):
            result['function_calls'].append((m.group(1), line_no))

        # 战利品表
        for m in loot_pattern.finditer(line):
            result['loot_table_refs'].append((m.group(2), line_no))

        # 结构
        for m in struct_pattern.finditer(line):
            result['structure_refs'].append((m.group(2), line_no))

    return result

def main():
    if not FUNCTION_DIR.exists():
        print(f"❌ 函数目录不存在: {FUNCTION_DIR}")
        sys.exit(1)

    # 收集所有引用
    all_registered = []       # (name, file, line)
    all_used = []             # (name, file, line)
    tag_refs = {'block': [], 'item': [], 'entity': [], 'function': []}
    pred_refs = []
    adv_refs = []
    func_calls = []
    loot_refs = []
    struct_refs = []

    for mc_file in FUNCTION_DIR.rglob("*.mcfunction"):
        result = scan_mcfunction(mc_file)
        # 记分板
        for name, line in result['scoreboard_registered']:
            all_registered.append((name, mc_file, line))
        for name, line in result['scoreboard_used']:
            all_used.append((name, mc_file, line))
        # 标签
        for tag_type in tag_refs:
            for name, line in result['tag_refs'][tag_type]:
                tag_refs[tag_type].append((name, mc_file, line))
        # 其他
        for name, line in result['predicate_refs']:
            pred_refs.append((name, mc_file, line))
        for name, line in result['advancement_refs']:
            adv_refs.append((name, mc_file, line))
        for name, line in result['function_calls']:
            func_calls.append((name, mc_file, line))
        for name, line in result['loot_table_refs']:
            loot_refs.append((name, mc_file, line))
        for name, line in result['structure_refs']:
            struct_refs.append((name, mc_file, line))

    # 统计基础数据
    registered_set = {name for name, _, _ in all_registered}
    used_set = {name for name, _, _ in all_used}
    unregistered = used_set - registered_set
    unused = registered_set - used_set

    print(f"📁 扫描了 {len(list(FUNCTION_DIR.rglob('*.mcfunction')))} 个 .mcfunction 文件")
    print(f"📝 注册的记分板: {len(registered_set)} 个")
    print(f"📝 使用的记分板: {len(used_set)} 个")

    # 输出未注册记分板（含位置）
    if unregistered:
        print("\n⚠️ 未注册的记分板（使用但未注册）：")
        for name in sorted(unregistered):
            positions = [f"{f}:{l}" for n, f, l in all_used if n == name]
            print(f"  - {name}")
            for pos in positions:
                print(f"      {pos}")
        print("\n建议在 init.mcfunction 中添加：")
        for name in sorted(unregistered):
            print(f"  scoreboard objectives add {name} dummy")
        print()

    # 输出未使用记分板
    if unused:
        print("[未使用] 以下记分板已注册但未使用：")
        for name in sorted(unused):
            positions = [f"{f}:{l}" for n, f, l in all_registered if n == name]
            print(f"  - {name}")
            for pos in positions:
                print(f"      {pos}")
        print()

    # 检查标签缺失（含位置）
    missing_tags = {'block': [], 'item': [], 'entity': [], 'function': []}
    for tag_type, refs in tag_refs.items():
        for name, file_path, line in refs:
            tag_file = TAG_DIR / tag_type / f"{name}.json"
            if not tag_file.exists():
                missing_tags[tag_type].append((name, file_path, line))
    if any(missing_tags.values()):
        print("⚠️ 缺失的标签：")
        for tag_type, items in missing_tags.items():
            if items:
                print(f"  [{tag_type}]")
                for name, file_path, line in items:
                    print(f"    - {name}  (引用自 {file_path}:{line})")
        print()

    # 检查谓词缺失
    missing_preds = []
    for name, file_path, line in pred_refs:
        pred_file = PREDICATE_DIR / f"{name}.json"
        if not pred_file.exists():
            missing_preds.append((name, file_path, line))
    if missing_preds:
        print("⚠️ 缺失的谓词：")
        for name, file_path, line in missing_preds:
            print(f"  - {name}  (引用自 {file_path}:{line})")
        print()

    # 检查进度缺失
    missing_advs = []
    for name, file_path, line in adv_refs:
        adv_file = ADVANCEMENT_DIR / f"{name}.json"
        if not adv_file.exists():
            missing_advs.append((name, file_path, line))
    if missing_advs:
        print("⚠️ 缺失的进度：")
        for name, file_path, line in missing_advs:
            print(f"  - {name}  (引用自 {file_path}:{line})")
        print()

    # 检查函数调用缺失
    missing_funcs = []
    for name, file_path, line in func_calls:
        func_file = FUNCTION_DIR / f"{name}.mcfunction"
        if not func_file.exists():
            missing_funcs.append((name, file_path, line))
    if missing_funcs:
        print("⚠️ 缺失的函数文件：")
        for name, file_path, line in missing_funcs:
            print(f"  - {name}  (引用自 {file_path}:{line})")
        print()

    # 检查战利品表缺失
    missing_loots = []
    for name, file_path, line in loot_refs:
        loot_file = LOOT_TABLE_DIR / f"{name}.json"
        if not loot_file.exists():
            missing_loots.append((name, file_path, line))
    if missing_loots:
        print("⚠️ 缺失的战利品表：")
        for name, file_path, line in missing_loots:
            print(f"  - {name}  (引用自 {file_path}:{line})")
        print()

    # 检查结构缺失
    missing_structs = []
    for name, file_path, line in struct_refs:
        struct_file = STRUCTURE_DIR / f"{name}.nbt"
        if not struct_file.exists():
            missing_structs.append((name, file_path, line))
    if missing_structs:
        print("⚠️ 缺失的结构文件：")
        for name, file_path, line in missing_structs:
            print(f"  - {name}  (引用自 {file_path}:{line})")
        print()

    # JSON 语法错误（直接显示文件路径）
    json_errors = []
    for json_file in PACK_ROOT.glob("data/**/*.json"):
        if json_file.parent == PACK_ROOT:
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            json_errors.append((json_file, e))
    if json_errors:
        print("⚠️ JSON 语法错误：")
        for file, err in json_errors:
            print(f"  {file}: {err}")
        print()

    # NBT 错误
    nbt_errors = []
    try:
        import nbtlib
    except ImportError:
        print("⚠️  nbtlib 未安装，跳过 NBT 检查。")
    else:
        for nbt_file in PACK_ROOT.glob("data/**/*.nbt"):
            try:
                nbtlib.load(nbt_file)
            except Exception as e:
                nbt_errors.append((nbt_file, e))
    if nbt_errors:
        print("⚠️ NBT 文件错误：")
        for file, err in nbt_errors:
            print(f"  {file}: {err}")
        print()

    # 统计汇总
    print("\n=== 统计汇总 ===")
    print(f"总函数文件数: {len(list(FUNCTION_DIR.rglob('*.mcfunction')))}")
    print(f"注册记分板: {len(registered_set)}")
    print(f"使用记分板: {len(used_set)}")
    print(f"未使用记分板: {len(unused)}")
    print(f"未注册记分板: {len(unregistered)}")
    tag_counts = {k: len(refs) for k, refs in tag_refs.items()}
    print(f"标签引用: {sum(tag_counts.values())} (block: {tag_counts['block']}, item: {tag_counts['item']}, entity: {tag_counts['entity']}, function: {tag_counts['function']})")
    print(f"谓词引用: {len(pred_refs)}")
    print(f"进度引用: {len(adv_refs)}")
    print(f"函数调用: {len(func_calls)}")
    print(f"战利品表引用: {len(loot_refs)}")
    print(f"结构引用: {len(struct_refs)}")
    print(f"JSON 语法错误: {len(json_errors)}")
    print(f"NBT 错误: {len(nbt_errors)}")

    total_issues = (len(unregistered) + sum(len(v) for v in missing_tags.values()) +
                    len(missing_preds) + len(missing_advs) + len(missing_funcs) +
                    len(missing_loots) + len(missing_structs) + len(json_errors) + len(nbt_errors))
    if total_issues == 0:
        print("\n✅ 所有检查通过！")
        sys.exit(0)
    else:
        print(f"\n❌ 发现 {total_issues} 个问题，请修复。")
        sys.exit(1)

if __name__ == "__main__":
    main()