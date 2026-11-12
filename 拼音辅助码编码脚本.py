#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# ───────────────────────────── 配 置 区 ──────────────────────────────
INPUT_PATH  = "base.dict.yaml"          # 单文件
OUTPUT_PATH = "outbase.dict.yaml"       # 单文件
OUTPUT_ERROR_CHAR_PATH = "error_char_pinyin_aux.txt"  # 记录缺少拼音/辅码 或 拼音/辅码有误的单字条目
AUX_FILE    = "辅助码.txt"              # 目前仅支持 **万象输入法 rime_wanxiang** 提供的单字表作为数据源，包含全拼拼音和六种辅码。可根据用户输入来选择辅码类型。
                                        # 格式：你\tnǐ;rx;rx;re;jy;wq;rx\t911   或  你\tnǐ;rx;rx;re;jy;wq;rx
                                        # https://github.com/amzxyz/rime_wanxiang/blob/wanxiang/dicts/chars.pro.dict.yaml
# ─────────────────────────────────────────────────────────────────────

class AuxCodeDictGenerator:
    """辅码词典生成器"""
    
    # 辅码类型映射
    AUX_CODE_TYPES = {
        '1': ('墨奇码', 'moqi', 0),
        '2': ('鹤形', 'flypy', 1),
        '3': ('自然码', 'zrm', 2),
        '4': ('虎码首末', 'tiger', 3),
        '5': ('五笔前2', 'wubi', 4),
        '6': ('汉心码', 'hanxin', 5)
    }
    
    # 需要跳过的标点符号集合，不匹配辅码
    PUNCTUATION = set('·+～！？，。…「」""“”：【】''『』')
    
    # 拼音音节表
    PINYIN_LIST = set(["a","ai","an","ang","ao","ba","bai","ban","bang","bao","bei","ben","beng","bi","bian","biao","bie","bin","bing","bo","bu","ca","cai","can","cang","cao","ce","cen","ceng","cha","chai","chan","chang","chao","che","chen","cheng","chi","chong","chou","chu","chua","chuai","chuan","chuang","chui","chun","chuo","ci","cong","cou","cu","cuan","cui","cun","cuo","da","dai","dan","dang","dao","de","dei","den","deng","di","dia","dian","diao","die","ding","diu","dong","dou","du","duan","dui","dun","duo","e","ei","en","eng","er","fa","fan","fang","fei","fen","feng","fiao","fo","fou","fu","ga","gai","gan","gang","gao","ge","gei","gen","geng","gong","gou","gu","gua","guai","guan","guang","gui","gun","guo","ha","hai","han","hang","hao","he","hei","hen","heng","hong","hou","hu","hua","huai","huan","huang","hui","hun","huo","ji","jia","jian","jiang","jiao","jie","jin","jing","jiong","jiu","ju","juan","jue","jun","ka","kai","kan","kang","kao","ke","kei","ken","keng","kong","kou","ku","kua","kuai","kuan","kuang","kui","kun","kuo","la","lai","lan","lang","lao","le","lei","leng","li","lia","lian","liang","liao","lie","lin","ling","liu","lo","long","lou","lu","luan","lüe","lun","luo","lü","m","ma","mai","man","mang","mao","me","mei","men","meng","mi","mian","miao","mie","min","ming","miu","mo","mou","mu","n","na","nai","nan","nang","nao","ne","nei","nen","neng","ni","nian","niang","niao","nie","nin","ning","niu","nong","nou","nu","nuan","nüe","nun","nuo","nü","o","ou","pa","pai","pan","pang","pao","pei","pen","peng","pi","pian","piao","pie","pin","ping","po","pou","pu","qi","qia","qian","qiang","qiao","qie","qin","qing","qiong","qiu","qu","quan","que","qun","ran","rang","rao","re","ren","reng","ri","rong","rou","ru","rua","ruan","rui","run","ruo","sa","sai","san","sang","sao","se","sen","seng","sha","shai","shan","shang","shao","she","shei","shen","sheng","shi","shou","shu","shua","shuai","shuan","shuang","shui","shun","shuo","si","song","sou","su","suan","sui","sun","suo","ta","tai","tan","tang","tao","te","tei","teng","ti","tian","tiao","tie","ting","tong","tou","tu","tuan","tui","tun","tuo","wa","wai","wan","wang","wei","wen","weng","wo","wu","xi","xia","xian","xiang","xiao","xie","xin","xing","xiong","xiu","xu","xuan","xue","xun","ya","yan","yang","yao","ye","yi","yin","ying","yo","yong","you","yu","yuan","yue","yun","za","zai","zan","zang","zao","ze","zei","zen","zeng","zha","zhai","zhan","zhang","zhao","zhe","zhei","zhen","zheng","zhi","zhong","zhou","zhu","zhua","zhuai","zhuan","zhuang","zhui","zhun","zhuo","zi","zong","zou","zu","zuan","zui","zun","zuo"])

    def __init__(self):
        self.char_aux_map = {}  # 单字辅码表 { 字: 辅码 }
        self.aux_code_index = 0  # 选择的辅码索引
        self.char_pinyin_map = {}  # 单字-拼音映射表 { 字: 拼音 }  由于本脚本主刷辅码兼刷拼音，不保证多音字的读音准确
        self.char_pinyin_set = set()  # 单字拼音集合 (字_拼音)  用于过滤错误读音

        self.err_char_pinyin_map = {}  # 单字表->拼音有误/缺少拼音条目 { 字: (拼音) }
        self.err_char_aux_list = []  # 单字表->辅码有误/缺少辅码条目
        self.err_char_misformatted_list = []  # 单字表->格式错误条目

        self.dict_missing_pinyin = set()  # 词典—>字符未知/缺少拼音/拼音有误
        self.dict_missing_pinyin_entries = []  # 词典-> 拼音异常词条 [(字符, 词条)]
        self.dict_missing_aux = set()  # 词典->字符未知/缺少辅码/辅码有误
        self.dict_missing_aux_entries = []  # 词典-> 辅码异常词条 [(字符, 词条)]
        self.dict_missing_entries = []  # 词典-> [(字符, 词条)]
        
        self.err_dict_entries = []  # 词典->出现异常错误的词条
        
    def load_char_table(self, char_table_path: str) -> bool:
        """加载单字表"""
        try:
            with open(char_table_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or self._is_header_line(line):
                        continue
                    parts = line.split('\t')
                    if len(parts) < 2:
                        self.err_char_misformatted_list.append(line)  # 格式错误
                        continue

                    # 解析拼音 + 选定的辅码
                    char = parts[0]
                    pinyin_codes = parts[1]
                    codes = pinyin_codes.split(';')
                    pinyin = codes[0] if len(codes) > 0 else None
                    aux = codes[self.aux_code_index + 1] if len(codes) > (self.aux_code_index + 1) else None

                    if self._is_valid_pinyin(pinyin):
                        self.char_pinyin_set.add(f"{char}_{pinyin}")  # 带声调拼音
                        no_tone = self._turn_pinyin_to_no_tone(pinyin)
                        self.char_pinyin_set.add(f"{char}_{no_tone}")  # 去声调拼音

                        if char not in self.char_pinyin_map:
                            self.char_pinyin_map[char] = pinyin
                    else:
                        self.err_char_pinyin_map[char] = pinyin  # 单字缺少拼音/拼音无效

                    if char not in self.char_aux_map:
                        if not self._is_valid_aux(aux):
                            self.char_aux_map[char] = ""  # 单字辅码为空/辅码无效
                            self.err_char_aux_list.append(line)
                        else:
                            self.char_aux_map[char] = aux
            
            print(f"\033[32m单字表加载完成，共加载 {len(self.char_pinyin_map)} 个字的拼音，{len(self.char_aux_map)} 个字的辅码\033[0m")
            
            if len(self.err_char_pinyin_map) > 0 or len(self.err_char_aux_list) > 0:
                print(f"\033[33m单字表部分条目存在格式错误，或单字缺少拼音/辅码，请检查格式是否正确\
                      \n支持的格式为：\n你\\tnǐ;rx;rx;re;jy;wq;rx\\t911\n或者：\n你\\tnǐ;rx;rx;re;jy;wq;rx\033[0m")
                self._save_error_char_entries()
            return True
            
        except Exception as e:
            print(f"加载单字表失败: {e}")
            return False
    
    def _is_header_line(self, line: str) -> bool:
        """判断是否为头部说明行"""
        headers = ['#', '---', 'name:', 'version:', 'sort:', '...']
        return any(line.startswith(h) for h in headers)

    def _turn_pinyin_to_no_tone(self, pinyin: str) -> Optional[str]:
        """带声调拼音转换为无声调"""
        if not pinyin:
            return None
        # 简化处理：去声调后判断是否符合汉语拼音音节
        # 对于极少数特殊音节的拼音，请见文件 OUTPUT_ERROR_CHAR_PATH 手动处理
        tone_map = {
            ord('ā'): 'a', ord('á'): 'a', ord('ǎ'): 'a', ord('à'): 'a',
            ord('ō'): 'o', ord('ó'): 'o', ord('ǒ'): 'o', ord('ò'): 'o',
            ord('ē'): 'e', ord('é'): 'e', ord('ě'): 'e', ord('è'): 'e',
            ord('ī'): 'i', ord('í'): 'i', ord('ǐ'): 'i', ord('ì'): 'i',
            ord('ū'): 'u', ord('ú'): 'u', ord('ǔ'): 'u', ord('ù'): 'u',
            ord('ǖ'): 'ü', ord('ǘ'): 'ü', ord('ǚ'): 'ü', ord('ǜ'): 'ü',
            ord('ḿ'): 'm', ord('ń'): 'n', ord('ň'): 'n', ord('ǹ'): 'n'
        }
        no_tone = pinyin.translate(tone_map)
        # 处理多字符
        no_tone = no_tone.replace("m̄", "m").replace("m̀", "m")
        return no_tone

    def _is_valid_pinyin(self, pinyin: str) -> bool:
        """判断拼音是否合法"""
        no_tone = self._turn_pinyin_to_no_tone(pinyin)
        if not no_tone:
            return False
        return bool(no_tone in self.PINYIN_LIST)
    
    def _is_valid_aux(self, aux: str) -> bool:
        """判断辅码是否合法"""
        if not aux or aux == "":
            return False
        parts = aux.split(',')
        pattern = r'^[a-zA-Z]+$'
        for part in parts:
            if not bool(re.match(pattern, part)):
                return False
        return True

    def _save_error_char_entries(self):
        """保存单字表的错误词条"""
        error_file = Path(OUTPUT_ERROR_CHAR_PATH).stem + ".txt"
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write("=== 缺少拼音/疑似拼音有误的单字 ===\n\n")
            for char, (pinyin) in self.err_char_pinyin_map.items():
                f.write(f"\t# 单字：{char}\t# 拼音: {pinyin}\n")

            f.write("\n\n\n\n\n\n=== 缺少辅码/疑似辅码有误的单字 ===\n\n")
            for entry in self.err_char_aux_list:
                f.write(f"\t# 条目: {entry}\n")

            f.write("\n\n\n\n\n\n=== 其他格式错误的条目 ===\n\n")
            for entry in self.err_char_misformatted_list:
                f.write(f"\t# 条目: {entry}\n")

            f.write(f"\n总计: {len(self.err_char_pinyin_map)} 个字符缺少拼音/疑似拼音有误\n")
            f.write(f"总计: {len(self.err_char_aux_list)} 个字符缺少辅码/疑似辅码有误\n")
            f.write(f"总计: {len(self.err_char_misformatted_list)} 个条目的格式错误\n")
            print(f"\n\033[33m单字表的错误词条已保存到: {OUTPUT_ERROR_CHAR_PATH}\033[0m")

    def process_dictionary(self, input_path: str, output_path: str, 
                         dict_type: str) -> bool:
        """处理词典文件"""
        try:
            # 先读取所有行
            with open(input_path, 'r', encoding='utf-8') as f_in:
                all_lines = f_in.readlines()
            
            # 写入输出文件
            with open(output_path, 'w', encoding='utf-8') as f_out:
                # 透传文件头部信息
                header_end_index = 0
                for i, line in enumerate(all_lines):
                    line_stripped = line.strip()
                    if self._is_header_line(line_stripped):
                        f_out.write(line)
                        header_end_index = i + 1
                    else:
                        break
                # 处理词条
                for i in range(header_end_index, len(all_lines)):
                    line = all_lines[i].rstrip('\n')
                    if not line.strip():
                        f_out.write(line + '\n')
                        continue
                    try:
                        new_entry = self._process_entry(line, dict_type)
                        f_out.write(new_entry + '\n')
                    except Exception as e:
                        # 保留原词条并记录错误
                        f_out.write(line + '\n')
                        self.err_dict_entries.append((line, str(e)))
            
            print(f"\033[32m词典处理完成，输出到: {output_path}\033[0m")

            if len(self.dict_missing_pinyin) > 0 or len(self.dict_missing_aux) > 0:
                self._save_missing_chars(output_path)
            if len(self.err_dict_entries) > 0:
                print(f"\033[33m发现 {len(self.err_dict_entries)} 个错误词条\033[33m")
                self._save_error_entries(output_path)
            return True
            
        except Exception as e:
            print(f"处理词典失败: {e}")
            return False
    
    def _process_entry(self, line: str, dict_type: str) -> str:
        """处理单个词条"""
        parts = line.split('\t')
        if dict_type == '1':  # 仅包含词语
            word = parts[0]
            pinyin_aux = self._generate_pinyin_aux(word, line)
            return f"{word}\t{pinyin_aux}\t"
        
        elif dict_type == '2':  # 包含词语、拼音、权重（可选）
            if len(parts) < 2:
                raise ValueError(f"词条格式错误: {line}")
            word = parts[0]
            pinyins = parts[1].split(' ')
            weight = parts[2] if len(parts) > 2 and parts[2].strip() else None

            pinyin_aux_list = self._generate_aux_with_pinyin(word, pinyins, line)
            result = f"{word}\t{' '.join(pinyin_aux_list)}\t"  # 缺少权重时，保留结尾制表符
            if weight:
                result += f"{weight}"
            return result
        
        else:
            raise ValueError(f"未知的词典类型: {dict_type}")
    
    def _generate_pinyin_aux(self, word: str, line: str) -> str:
        """为词语生成拼音和辅码"""
        pinyin_aux_list = []

        for char in word:
            if char in self.PUNCTUATION:  # 跳过标点符号
                continue

            # 加载的单字表已经过滤了异常拼音和异常辅码，此处不需要额外判断
            pinyin = self._get_pinyin_code(char)
            aux = self._get_aux_code(char)
            if not pinyin or pinyin == "":
                # 字符未知/缺少拼音/拼音无效
                self.dict_missing_pinyin.add(char)
                self.dict_missing_pinyin_entries.append((line, char))
                pinyin = ""
            if not aux or aux == "":
                # 字符未知/缺少辅码/辅码无效
                self.dict_missing_aux.add(char)
                self.dict_missing_aux_entries.append((line, char))
                aux = ""

            pinyin_aux_list.append(f"{pinyin};{aux}")  # 即使拼音/辅码为空，依然保留分隔符
        
        return ' '.join(pinyin_aux_list)
        
    def _get_pinyin_code(self, char: str) -> Optional[str]:
        """获取字符的辅码"""
        if char in self.char_pinyin_map:
            return self.char_pinyin_map[char]
        return None
    
    def _get_aux_code(self, char: str) -> Optional[str]:
        """获取字符的辅码"""
        if char in self.char_aux_map:
            return self.char_aux_map[char]
        return None

    def _generate_aux_with_pinyin(self, word: str, pinyins: List[str], line: str) -> List[str]:
        """结合已有的拼音，生成带辅码的拼音"""
        pinyin_aux_list = []  # 带辅码的拼音
        char_index = 0
        for char in word:
            if char in self.PUNCTUATION:  # 跳过标点符号
                continue
            if char_index >= len(pinyins):  # 字数多于拼音音节数
                self.err_dict_entries.append((line, "字数 > 拼音音节数"))
                break

            pinyin = pinyins[char_index]
            aux = self._get_aux_code(char)
            if not self._is_valid_pinyin(pinyin) or not self._is_pinyin_match_char(pinyin, char):
                # 缺少拼音/拼音无效 或 拼音与单字不匹配，仅记录，仍保留原拼音
                self.dict_missing_pinyin.add(char)
                self.dict_missing_pinyin_entries.append((line, char))
            if not aux or aux == "":
                # 缺少辅码/辅码无效，辅码留空
                self.dict_missing_aux.add(char)
                self.dict_missing_aux_entries.append((line, char))
                aux = ""

            pinyin_aux_list.append(f"{pinyin};{aux}")  # 即使拼音/辅码为空，依然保留分隔符
            char_index += 1
        
        if char_index < len(pinyins):  # 字数少于拼音音节数
            self.err_dict_entries.append((line, "字数 < 拼音音节数"))

        return pinyin_aux_list

    def _is_pinyin_match_char(self, pinyin: str, char: str) -> bool:
        """拼音与单字是否匹配"""
        if not char or not pinyin or pinyin == "":
            return False
        char_pinyin = f"{char}_{pinyin}"
        return bool(char_pinyin in self.char_pinyin_set)

    def _save_missing_chars(self, output_path: str):
        """保存缺少拼音/编码/字符的词条"""
        missing_file = Path(output_path).stem + '_missing_chars.txt'
        with open(missing_file, 'w', encoding='utf-8') as f:
            # 重构字典映射
            pinyin_char_to_entries = {}  # 缺少拼音/拼音无效/未知字符的词条 { 字符: [ 词条1, 词条2 ] }
            aux_char_to_entries = {}  # 缺少辅码/辅码无效/未知字符的词条 { 字符: [ 词条1, 词条2 ] }
            for entry, char in self.dict_missing_pinyin_entries:
                if char in self.dict_missing_pinyin:
                    if char not in pinyin_char_to_entries:
                        pinyin_char_to_entries[char] = []
                    pinyin_char_to_entries[char].append(entry)
            for entry, char in self.dict_missing_aux_entries:
                if char in self.dict_missing_aux:
                    if char not in aux_char_to_entries:
                        aux_char_to_entries[char] = []
                    aux_char_to_entries[char].append(entry)
            
            f.write("=== 缺少拼音/疑似拼音有误/含未知字符的相关词条 ===\n\n")
            for char in sorted(pinyin_char_to_entries.keys()):
                f.write(f"\t字符: 【{char}】\n")
                f.write("\t\t相关词条:\n")
                # 输出该字符相关的所有词条
                for entry in pinyin_char_to_entries[char]:
                    f.write(f"\t\t\t{entry}\n")
                f.write("\n\t" + "-" * 50 + "\n\n")

            f.write("\n\n\n\n\n\n=== 缺少辅码/疑似辅码有误/含未知字符的相关词条 ===\n\n")
            for char in sorted(aux_char_to_entries.keys()):
                f.write(f"\t字符: 【{char}】\n")
                f.write("\t\t相关词条:\n")
                # 输出该字符相关的所有词条
                for entry in aux_char_to_entries[char]:
                    f.write(f"\t\t\t{entry}\n")
                f.write("\n\t" + "-" * 50 + "\n\n")
            
            # 输出统计信息
            f.write(f"\n总计: {len(self.dict_missing_pinyin)} 个字符未知/缺少拼音/疑似拼音有误\n")
            f.write(f"总计: {len(self.dict_missing_aux)} 个字符未知/缺少辅码/疑似辅码有误\n")
            f.write(f"影响词条数: {len([e for e in self.dict_missing_entries if isinstance(e[1], str) and len(e[1]) == 1])}\n")
        
        if len(self.dict_missing_pinyin) > 0:
            print(f"\033[33m发现 {len(self.dict_missing_pinyin)} 个缺少拼音/疑似拼音有误/未知的字符\033[33m")
        if len(self.dict_missing_aux) > 0:
            print(f"\033[33m发现 {len(self.dict_missing_aux)} 个缺少辅码/疑似辅码有误/未知的字符\033[33m")
        print(f"\033[33m缺少拼音/辅码/未知的字符及词条已保存到: {missing_file}\033[0m")
    
    def _save_error_entries(self, output_path: str):
        """保存其他异常词条"""
        error_file = Path(output_path).stem + '_errors.txt'
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write("=== 其他异常词条 ===\n\n")
            for entry, err_msg in self.err_dict_entries:
                f.write(f"\t{entry}\t# 错误: {err_msg}\n")
        print(f"\033[33m其他异常词条已保存到: {error_file}\033[0m")


def main():
    """主函数"""
    print("=== 带辅码词典生成器 ===")
    
    generator = AuxCodeDictGenerator()

    # 获取用户输入
    print("\n辅码类型:")
    for key, (name, _, _) in generator.AUX_CODE_TYPES.items():
        print(f"{key}. {name}")
    aux_code_type = input("请选择辅码类型 (1-6): ").strip()    
    if aux_code_type in generator.AUX_CODE_TYPES:
        _, _, generator.aux_code_index = generator.AUX_CODE_TYPES[aux_code_type]  # 设置辅码索引
    else:
        print(f"无效的辅码类型: {aux_code_type}")
        return

    print("\n词典类型:")
    print("1. 仅包含词语，需要生成拼音+辅码")
    print("2. 包含词语+拼音（+权重），需要生成辅码")
    dict_type = input("请选择输入的词典类型 (1-2): ").strip()
    if not dict_type == '1' and not dict_type == '2':
        print("无效的词典类型！")
        return
    
    char_table_path = input(f"\n请输入码表路径 (默认: {AUX_FILE}): ").strip() or AUX_FILE
    if not generator.load_char_table(char_table_path):  # 检查并加载单字表
        return

    input_dict_path = input(f"请输入输入词库路径（默认：{INPUT_PATH}）: ").strip() or INPUT_PATH
    output_dict_path = input(f"请输入输出词库路径（默认：{OUTPUT_PATH}）: ").strip() or OUTPUT_PATH
    
    # 处理词典
    generator.process_dictionary(input_dict_path, output_dict_path, dict_type)


# ---------- 主入口 ----------
if __name__ == "__main__":
    main()
