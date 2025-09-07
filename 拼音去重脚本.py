# 功能：
#   找到并去重指定音节范围且音节数完全相同的词组
#
# 命令行：
#    python filter_dict.py <输入的词库文件> <重复词条文件> <去重后输出的词库文件> <最小音节数> <最大音节数>
#   
# 示例：       
#   python filter_dict.py base.dict.yaml duplicated.txt output.dict.yaml 5 20
#   解释：输入词库为 base.dict.yaml，检查音节数在5~20的所有词条，音节完全相同的重复词条会输出到 duplicated.txt，去重后的词库输出为 output.dict.yaml
#
#   ⚠️⚠️⚠️注意⚠️⚠️⚠️
#   去重结果一定要手动校对，需要还原词条的场景示例：
#   1. 指向不同的内容的谐音词条，应进行保留。
#   2. 同一人物/事物/...的不同译名，应适当保留。
#   3. 音节少的词，建议适当保留。
#   4. 还原简化作品名。某些作品名词条完全由汉字组成，既有合适的译名，又有被直接简化为异体字的、传播度低的简化名。优先保留（有一定传播度的）原词条名，以及译后词条。
#       例1：纱痳<简化词条> -> 紗痲<原词条> + 纱麻<译后词条>
#       例2：东京电脳探侦団<简化词条> -> 東京電脳探偵団<原词条> + 东京电脑侦探团<译后词条>
#       例3：名探侦连続杀人事件<简化词条> -> 名探偵連続殺人事件<原词条> - 名侦探连续杀人事件<译后词条>
#

import os, re, shutil
import sys
from collections import defaultdict
from typing import Dict, List, Set

def process_phrase_library(input_file, output_dup_file, output_unique_file, min_indice, max_indice):
    # 读取所有行
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f]

        pronunciation_groups = defaultdict(list)  # 存储发音分组：{拼音: [(行索引, 原始行)]}
        keep_indices = set()  # 标记需要保留的行：格式错误行、非N音节行、每组首次出现的行
        target_idx_pinyin = set()  # 存储需要去重行的行索引-拼音

        # 第一遍处理：收集所有格式正确且音节数为N的行
        for idx, line in enumerate(lines):
            if is_header_line(line):  # 跳过头部说明行
                continue
            
            # 兼容格式：<词语>\t<拼音>  或  <词语>\t<拼音>\t<词条权重>
            parts = line.split('\t')
            if len(parts) != 2 and len(parts) != 3:  # 格式错误行，保留并跳过
                keep_indices.add(idx)
                continue

            pinyin = parts[1]
            if pinyin == "":
                keep_indices.add(idx)
                continue

            syllables = pinyin.split()  # 音节组
            if len(syllables) < min_indice or len(syllables) > max_indice:  # 音节数不符，保留并跳过
                keep_indices.add(idx)
                continue
                
            target_idx_pinyin.add((idx, pinyin))
            pronunciation_groups[pinyin].append((idx, line))

        # 提取有重复的组（至少2个词组），并按组的第一行行号排序（保持原顺序）
        duplicate_groups = []
        for group in pronunciation_groups.values():
            if len(group) > 1:
                # 按行索引排序并记录
                sorted_group = sorted(group, key=lambda x: x[0])
                duplicate_groups.append(sorted_group)
        duplicate_groups.sort(key=lambda group: group[0][0])

    # 写入重复词组文件（组间空行分隔）
    with open(output_dup_file, 'w', encoding='utf-8') as f:
        for group in duplicate_groups:
            for _, line in group:
                f.write(line + '\n')
            f.write('\n')  # 组间空行

        # 第二遍处理：输出去重后的词库
        for _, group in enumerate(target_idx_pinyin):
            idx, pinyin = group
            if idx == pronunciation_groups[pinyin][0][0]:
                # 对于重复发音组，优先按原文件顺序保留首行
                keep_indices.add(idx)

    # 写入去重后的词库文件
    with open(output_unique_file, 'w', encoding='utf-8') as f:
        for idx, line in enumerate(lines):
            if is_header_line(line) or idx in keep_indices:
                f.write(line + '\n')

def is_header_line(line: str) -> bool:
    """判断是否为头部说明行"""
    headers = ['#', '---', 'name:', 'version:', 'sort:', '...']
    return any(line.startswith(h) for h in headers)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("参数不匹配！\n用法: python script.py <输入的词库文件> <重复词条文件> <去重后输出的词库文件> <最小音节数> <最大音节数>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"输入的词库文件不存在: {input_file}")
        sys.exit(1)

    output_dup_file = sys.argv[2]
    output_unique_file = sys.argv[3]
    min_indice = int(sys.argv[4])
    max_indice = int(sys.argv[5])
    if min_indice < 1 or min_indice > max_indice:
        print(f"输入的音节数错误: 最小音节数: {min_indice}, 最大音节数：{max_indice}")
        sys.exit(1)
    
    process_phrase_library(input_file, output_dup_file, output_unique_file, min_indice, max_indice)
    print(f"处理完成！重复词组已保存至: {output_dup_file}")
    print(f"去重词库已保存至: {output_unique_file}")
