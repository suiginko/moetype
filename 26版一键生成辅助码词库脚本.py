#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多功能词库处理工具（集成无声调转换功能）
────────────────────────────────────────────────────────
功能：
0. 刷辅助码且不会修改词库的拼音部分
1. 支持多个单字辅助码表
2. 生成带辅助码的词库（每个辅助码表对应一个输出文件）
3. 生成纯净拼音词库（去除辅助码，保留声调）
4. 生成交换格式词库（拼音在前，汉字在后，保留权重，txt格式）
5. 生成无声调纯净词库（去除辅助码且去除声调，特殊处理“嗯”等字符）
6. 支持跳过非汉字字符（包括所有Unicode汉字扩展区和可选的日语假名）
7. 支持自定义字符白名单（允许手动指定需要刷码的特殊字符）
8. 优化：若无对应辅助码但属于有效字符，拼音结尾补分号占位
"""

from __future__ import annotations
import os, re, shutil
from pathlib import Path
from typing import Dict, List, Tuple, Set
from tqdm import tqdm

# ─────────────── 配 置 区 ────────────────
INPUT_PATH = "C:/Users/Hg/词库转换/输入词库"           # 输入词库目录或文件
AUX_TABLES_DIR = "C:/Users/Hg/词库转换/辅助码表"       # 辅助码表目录
OUTPUT_ROOT = "C:/Users/Hg/词库转换/输出词库"          # 输出根目录
INCLUDE_KANA = False                               # 是否将日语假名视为需要刷辅助码的汉字（默认为False）

# 自定义字符白名单：在这里填入你想要刷辅助码的其他字符（如：々）
# 即使这些字符不在汉字或假名范围内，只要在这里出现，就会被尝试刷码或添加分号占位
CUSTOM_CHARS = "々"                                 
# ──────────────────────────────────────

# ─────────────── 声调转换配置 (集成自无声调脚本) ────────────────
TONE_MAP = {
    'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
    'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
    'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
    'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
    'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
    'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v',
    'ń': 'n', 'ň': 'n', 'ǹ': 'n',
    'ḿ': 'mu',  # 特殊规则：ḿ转为mu
    'm̄': 'mu', 'm̀': 'mu', 'ḿ': 'mu', 'm̌': 'mu'
}

SPECIAL_WORDS = {
    '嗯': 'en',  # 特殊规则："嗯"转为"en"
}
# ────────────────────────────────────────────────────────────

# Unicode汉字范围（包括所有扩展区）
HANZI_RANGES = [
    (0x4E00, 0x9FFF),     # 基本汉字
    (0x3400, 0x4DBF),     # 扩展A
    (0x20000, 0x2A6DF),   # 扩展B
    (0x2A700, 0x2B73F),   # 扩展C
    (0x2B740, 0x2B81F),   # 扩展D
    (0x2B820, 0x2CEAF),   # 扩展E
    (0x2CEB0, 0x2EBEF),   # 扩展F
    (0x30000, 0x3134F),   # 扩展G
    (0x31350, 0x323AF),   # 扩展H
    (0x2EBF0, 0x2EE5D),   # 扩展I
    (0x323B0, 0x33479),   # 扩展J
]

# 日语假名范围（如果启用）
KANA_RANGES = [
    (0x3040, 0x309F),     # 平假名
    (0x30A0, 0x30FF),     # 片假名
    (0x31F0, 0x31FF),     # 片假名拼音扩展
]

# 全局配置
AUX_SEP_REGEX = r'[;\[]'
yaml_heads = ('---', 'name:', 'version:', 'sort:', '...')
SKIP_FILES = {'compatible.dict.yaml', 'corrections.dict.yaml', 'people.dict.yaml', 'encnnum.dict.yaml'}

def is_hanzi(char: str) -> bool:
    """检查字符是否为汉字（包括所有Unicode扩展区）"""
    cp = ord(char)
    for start, end in HANZI_RANGES:
        if start <= cp <= end:
            return True
    return False

def is_kana(char: str) -> bool:
    """检查字符是否为日语假名"""
    if not INCLUDE_KANA:
        return False
        
    cp = ord(char)
    for start, end in KANA_RANGES:
        if start <= cp <= end:
            return True
    return False

def is_custom_char(char: str) -> bool:
    """检查字符是否在用户自定义白名单中"""
    return char in CUSTOM_CHARS

def is_valid_char(char: str) -> bool:
    """检查字符是否为有效字符（汉字、可选的假名、或自定义字符）"""
    return is_hanzi(char) or is_kana(char) or is_custom_char(char)

def is_dir_like(p: str) -> bool:
    """判断路径是否像目录"""
    return (p.endswith(('/', '\\')) or 
            os.path.isdir(p) or 
            not os.path.splitext(p)[1])

def create_output_dir():
    """创建输出目录"""
    Path(OUTPUT_ROOT).mkdir(parents=True, exist_ok=True)
    return OUTPUT_ROOT

def load_aux_tables() -> Dict[str, Dict[str, str]]:
    """加载所有辅助码表"""
    aux_tables = {}
    print(f"扫描辅助码表目录: {AUX_TABLES_DIR}")
    
    for filename in os.listdir(AUX_TABLES_DIR):
        if not filename.endswith(('.yaml', '.txt')):
            continue
            
        table_name = os.path.splitext(filename)[0]
        filepath = os.path.join(AUX_TABLES_DIR, filename)
        
        if not os.path.isfile(filepath):
            continue
            
        aux_map = {}
        with open(filepath, encoding='utf-8') as f:
            for line in f:
                if not line.strip() or line.startswith('#') or line.startswith('---'):
                    continue
                    
                parts = line.rstrip('\n').split('\t')
                if len(parts) < 2 or len(parts[0]) != 1:
                    continue
                    
                char, seg = parts[:2]
                if ';' in seg:
                    aux_code = seg.split(';', 1)[1]
                else:
                    aux_code = seg
                    
                aux_map[char] = aux_code
        
        aux_tables[table_name] = aux_map
        print(f"✓ 加载辅助码表 [{table_name}]: {len(aux_map)} 条")
    
    if not aux_tables:
        print("⚠ 警告: 未找到任何辅助码表文件")
        
    return aux_tables

def clean_aux_from_seg(seg: str) -> str:
    """从单个拼音段中移除辅助码"""
    parts = re.split(AUX_SEP_REGEX, seg, 1)
    return parts[0]  # 只返回拼音部分

# ─────────────── 无声调核心逻辑 (集成自无声调脚本) ────────────────
def remove_tones(pinyin_str: str) -> str:
    """移除拼音中的声调符号"""
    if pinyin_str in SPECIAL_WORDS:
        return SPECIAL_WORDS[pinyin_str]
    
    if pinyin_str.startswith('嗯'):
        parts = pinyin_str.split()
        if parts[0] == '嗯':
            parts[0] = 'en'
            return ' '.join(parts)
    
    result = []
    for seg in pinyin_str.split():
        # 先移除可能存在的辅助码干扰（虽然流程上会先清辅助码，但这里做双重保险）
        seg = clean_aux_from_seg(seg)
        
        if seg in ('ńg', 'ňg', 'ǹg', 'ń', 'ň', 'ǹ'):
            result.append('en')
            continue
            
        clean_seg = ''.join(TONE_MAP.get(c, c) for c in seg)
        if clean_seg == 'ng' or clean_seg == 'n':
            clean_seg = 'en'
        result.append(clean_seg)
    return ' '.join(result)
# ────────────────────────────────────────────────────────────

def is_userdb_head(line: str) -> bool:
    """检测是否是Rime用户词典头"""
    return '#@/db_type\tuserdb' in line or '# Rime user dictionary' in line

def process_line_for_pure(line: str, userdb: bool) -> Tuple[str, bool]:
    """处理行以生成纯净词库"""
    if line.startswith(yaml_heads) or line.startswith('#'):
        return line, userdb
        
    if not line.strip():
        return line, userdb
        
    cols = line.split('\t')
    
    if userdb and len(cols) > 0:
        segs = cols[0].split()
        cleaned_segs = [clean_aux_from_seg(seg) for seg in segs]
        cols[0] = ' '.join(cleaned_segs)
    elif len(cols) > 1:
        segs = cols[1].split()
        cleaned_segs = [clean_aux_from_seg(seg) for seg in segs]
        cols[1] = ' '.join(cleaned_segs)
    
    return '\t'.join(cols), userdb

def process_line_for_toneless(line: str, userdb: bool) -> Tuple[str, bool]:
    """处理行以生成无声调纯净词库"""
    if line.startswith(yaml_heads) or line.startswith('#'):
        return line, userdb
    if not line.strip():
        return line, userdb
        
    cols = line.split('\t')
    idx = 0 if userdb else 1
    
    if len(cols) > idx:
        cols[idx] = remove_tones(cols[idx])
        
    return '\t'.join(cols), userdb

def process_line_for_aux(line: str, aux_map: Dict[str, str], userdb: bool) -> Tuple[str, bool]:
    """处理行以添加辅助码（包含分号占位优化）"""
    if line.startswith(yaml_heads) or line.startswith('#'):
        return line, userdb
        
    if not line.strip():
        return line, userdb
        
    cols = line.split('\t')
    word = cols[1] if userdb and len(cols) > 1 else cols[0]
    
    # 针对普通格式或UserDB格式分别处理
    idx_to_process = 0 if userdb else 1
    
    if len(cols) > idx_to_process:
        segs = cols[idx_to_process].split()
        py_idx = 0
        
        for ch in word:
            # 只有白名单内的字符（汉字/假名/自定义）才会消耗拼音段
            if not is_valid_char(ch):
                continue
                
            if py_idx < len(segs):
                py_part = clean_aux_from_seg(segs[py_idx])
                # 获取辅助码，若没有则为空字符串，但分号始终保留
                aux_code = aux_map.get(ch, "")
                segs[py_idx] = f"{py_part};{aux_code}"
                py_idx += 1
                
        cols[idx_to_process] = ' '.join(segs)
    
    return '\t'.join(cols), userdb

def process_line_for_swapped(line: str, userdb: bool) -> Tuple[str, bool]:
    """处理行以生成交换格式"""
    if line.startswith(yaml_heads) or line.startswith('#'):
        return "", userdb
        
    if not line.strip():
        return "", userdb
        
    cols = line.split('\t')
    if len(cols) < 2:
        return "", userdb
        
    if userdb:
        py_str = cols[0]
        word = cols[1]
    else:
        word = cols[0]
        py_str = cols[1]
    
    others = cols[2:] if len(cols) > 2 else []
    py_segs = py_str.split()
    cleaned_py = ' '.join([clean_aux_from_seg(seg) for seg in py_segs])
    
    new_cols = [cleaned_py, word] + others
    return "\t".join(new_cols), userdb

def process_file(src: str, dest: str, process_func, aux_map=None):
    """处理单个文件"""
    userdb = False
    with open(src, encoding='utf-8') as s, open(dest, 'w', encoding='utf-8') as d:
        for raw in s:
            line = raw.rstrip('\n')
            if is_userdb_head(line):
                userdb = True
            if aux_map:
                processed_line, userdb = process_func(line, aux_map, userdb)
            else:
                processed_line, userdb = process_func(line, userdb)
            if processed_line:
                d.write(processed_line + '\n')

def get_output_filename(src_path: str, output_dir: str, prefix: str = "", suffix: str = "") -> str:
    """生成输出文件名"""
    base_name = os.path.basename(src_path)
    name, ext = os.path.splitext(base_name)
    new_name = f"{prefix}{name}{suffix}{ext}"
    if "exchanged_" in prefix:
        new_name = f"{prefix}{name}{suffix}.txt"
    return os.path.join(output_dir, new_name)

def process_input(input_path: str, output_dir: str, prefix: str = "", suffix: str = "", process_func=None, aux_map=None) -> List[str]:
    """处理输入路径（文件或目录）"""
    generated_files = []
    if os.path.isfile(input_path):
        dest = get_output_filename(input_path, output_dir, prefix, suffix)
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        process_file(input_path, dest, process_func, aux_map)
        generated_files.append(dest)
        print(f"✓ 完成 {os.path.basename(input_path)} → {os.path.basename(dest)}")
    else:
        tasks = []
        for root, _, files in os.walk(input_path):
            for fn in files:
                if not fn.endswith(('.txt', '.yaml')) or fn in SKIP_FILES:
                    continue
                src_file = os.path.join(root, fn)
                dest_file = get_output_filename(src_file, output_dir, prefix, suffix)
                tasks.append((src_file, dest_file))
        if not tasks: return []
        bar = tqdm(tasks, desc="处理文件", unit="file", ncols=90)
        for src, dest in bar:
            bar.set_postfix(file=os.path.basename(src))
            Path(dest).parent.mkdir(parents=True, exist_ok=True)
            process_file(src, dest, process_func, aux_map)
            generated_files.append(dest)
            tqdm.write(f"✓ 完成 {os.path.basename(src)} → {os.path.basename(dest)}")
    return generated_files

def generate_pure_pinyin(input_path: str, output_dir: str) -> List[str]:
    """生成纯净拼音词库"""
    print("\n" + "="*50 + "\n步骤1: 生成纯净拼音词库 (保留声调)\n" + "="*50)
    return process_input(input_path, output_dir, "tone_", "", process_line_for_pure)

def generate_aux_pinyin(input_path: str, output_dir: str, aux_tables: Dict[str, Dict[str, str]]) -> List[str]:
    """生成带辅助码的词库"""
    if not aux_tables: return []
    print("\n" + "="*50 + "\n步骤2: 生成带辅助码的词库\n" + "="*50)
    generated_files = []
    for table_name, aux_map in aux_tables.items():
        print(f"\n▷ 处理辅助码表: {table_name}")
        files = process_input(input_path, output_dir, f"{table_name}_", "", process_line_for_aux, aux_map)
        generated_files.extend(files)
    return generated_files

def generate_swapped_pinyin(input_path: str, output_dir: str) -> List[str]:
    """生成交换格式词库"""
    print("\n" + "="*50 + "\n步骤3: 生成交换格式词库\n" + "="*50)
    return process_input(input_path, output_dir, "exchanged_", "", process_line_for_swapped)

def generate_toneless_pinyin(input_path: str, output_dir: str) -> List[str]:
    """生成无声调纯净词库"""
    print("\n" + "="*50 + "\n步骤4: 生成无声调纯净词库\n" + "="*50)
    return process_input(input_path, output_dir, "toneless_", "", process_line_for_toneless)

if __name__ == "__main__":
    output_dir = create_output_dir()
    aux_tables = load_aux_tables()
    
    # 原始功能
    pure_files = generate_pure_pinyin(INPUT_PATH, output_dir)
    aux_files = generate_aux_pinyin(INPUT_PATH, output_dir, aux_tables)
    swapped_files = generate_swapped_pinyin(INPUT_PATH, output_dir)
    
    # 新集成的无声调功能
    toneless_files = generate_toneless_pinyin(INPUT_PATH, output_dir)
    
    print("\n" + "="*50 + "\n✓ 处理完成！\n" + 
          f"• 输出目录: {output_dir}\n" + 
          "• 包含: 带调纯净(tone_)、带辅助码(表名_)、交换格式(exchanged_)、无声调(toneless_)\n" + 
          "• 缺失辅助码的有效字符已补分号占位\n" + "="*50)