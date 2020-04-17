#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/4/3 18:58
# @Author  : yangmingming
# @Site    : 
# @File    : project_check.py
# @Software: PyCharm
import logging
import os
import re
import wave
from CommenScript.update_data.vad import get_wav_start_end

logger = logging.getLogger("yangmingming")
log_path = os.path.dirname(os.getcwd()) + '/Logs/'
n = 1
log_name = log_path + str(n) + '-log.log'
while os.path.exists(log_name):
    n += 1
    log_name = log_path + str(n) + '-log.log'
fh = logging.FileHandler(log_name, mode='a', encoding="utf8")
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
logger.addHandler(fh)
logger.addHandler(console)


class ProjectCheck(object):
    def __init__(self):
        pass

    def check_file_complete(self, projec_path):
        """
        检查项目中文件完整性
        :param projec_path:
        :return:
        """
        logging.warning("project file check start")
        for root, dirs, files in os.walk(project_path):
            for file in files:
                name, suffix = os.path.splitext(file)
                if suffix in ["txt", "metadata", "wav"]:
                    wav_file = os.path.join(root, name + ".wav")
                    txt_file = os.path.join(root, name + ".txt")
                    meta_file = os.path.join(root, name + ".metadata")
                    for item in [wav_file, txt_file, meta_file]:
                        if not os.path.exists(item):
                            logger.error("{}\tdoes not exist".format(item))
        logging.warning("project file check end")

    def check(self, project_path):
        """
        检查项目
        :param project_path:
        :return:
        """
        logging.warning("Start")
        print(project_path)
        # self.check_file_complete(project_path)  # 检查文件的完整性
        # 将所有文件名放入list，检查是否有重复
        all_name_list = []
        for root, dirs, files in os.walk(project_path):
            for file_name in files:
                file = os.path.join(root, file_name)
                all_name_list.append(file)
                if file.endswith("wav"):
                    wav = WAV(file)
                    wav.check()
                elif file.endswith("metadata"):
                    meta = Metadata(file)
                    meta.check()
                elif file.endswith("txt"):
                    txt = TXT(file)
                    txt.check()
                else:
                    logger.error("{}\tfile type error".format(file))
        if not len(all_name_list) == len(set(all_name_list)):
            logger.error("{}\tfile name repeat".format(file))


class File(object):
    GROUP_REGEX = re.compile('(?P<group>[G|Z]\d+)[A-F\d_]*(?P<session>S\d+)\.')

    def __init__(self, filepath):
        self.filepath = filepath
        self.flag = True
        r = self.GROUP_REGEX.search(os.path.basename(filepath))
        if r:
            self.group = r.group('group').strip()
        else:
            self.group = os.path.basename(filepath)

        # 用户定义的合法字符，有些字符是特殊字符但是在某些语言中合法，例如 "、" 在日语中合法
        self.custom_leg_symbol = ['、', '々']
        # 获取特殊字符
        with open("err_symbol.txt", 'r', encoding='utf8')as f:
            self.err_symbol = f.read()

            # 将用户认为合法的字符剔除错误字符检验
            for single_char in self.custom_leg_symbol:
                self.err_symbol = self.err_symbol.replace(single_char, "")

        # 定义合法噪音符号
        self.noisy_list = ['[[lipsmack]]', '[[cough]]', '[[sneeze]]', '[[breath]]', '[[background]]', '[[laugh]]',
                           '[r]', '[p]', '[b]', '[a]', '[m]', '[n]']

    def read_file(self):
        """
         读取文件,捕获编码，如果不是utf8 抛出异常
        :return:
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return f.readlines()
        except UnicodeDecodeError as e:
            logger.error("{}\t not encode utf-8".format(self.filepath))


class TXT(File):

    def remove_noisy(self, input_str):
        for noisy in self.noisy_list:
            input_str = input_str.replace(noisy, ' ')
        return input_str

    def check_in(self, input_str, path):
        input_str = self.remove_noisy(input_str)
        res1 = re.findall('\\[\\(\\(.*?\\)\\)\\]', input_str)
        pattern = self.err_symbol
        if len(res1) > 0:
            for each in res1:
                new_str = each[3:-3]
                new_str = self.remove_noisy(new_str)
                special_symbol = re.findall(pattern, new_str)
                if special_symbol:
                    logger.error(f'{path}\tin contain symbol {special_symbol}\t{input_str}')

        res2 = re.findall('\\[\\/.*?\\/\\]', input_str)
        if len(res2) > 0:
            for each in res2:
                new_str = each[2:-2]
                new_str = self.remove_noisy(new_str)
                special_symbol = re.findall(pattern, new_str)
                if special_symbol:
                    logger.error(f'{path}\tin contain symbol {special_symbol}\t{input_str}')

    def check_out(self, input_str, path):
        # 先去掉所有噪音符号
        new_str = self.remove_noisy(input_str)
        new_str = new_str.replace('[/', ' ').replace('/]', ' ').replace('[((', ' ').replace('))]', ' ')
        pattern = self.err_symbol
        special_symbol = re.findall(pattern, new_str)
        if special_symbol:
            logger.error(f'{path}\tout contain symbol {special_symbol}\t{input_str}')

    def check_noisy(self, input_str, path):
        """
        检查噪音符号
        :param input_str:
        :param path:
        :return:
        """
        for noisy in self.noisy_list:
            input_str = input_str.replace(noisy, ' ')
        for noisy in self.noisy_list:
            noisy_new = noisy.replace('[[', '').replace(']]', '')
            if noisy_new in input_str:
                logger.error(f'{path}\tcontain other noisy {noisy_new}\t{input_str}')

    def is_double_str(self, content):
        """
        是否包含全角
        :param lines:
        :return:
        """
        double_s = []
        double_str = lambda x: ord(x) == 0x3000 or 0xFF01 <= ord(x) <= 0xFF5E
        for x in content:
            if double_str(x):
                double_s.append(x)
        if double_s:
            logger.error("{}\t Has double str(quan jiao) is {}\t{}".format(self.filepath, double_s, content))

    def is_one_line(self, lines: list):
        """
         判断是否为一行
        :param lines: 文本行
        :return:
        """
        if len(lines) == 0:
            logger.error("{}\t the file is empty".format(self.filepath))
        elif len(lines) > 1:
            logger.error("{}\t the file is Multi-line".format(self.filepath))
        else:
            content = lines[0].strip()
            if not content:
                logger.error("{}\t the file is line break".format(self.filepath))

    def is_have_digit(self, content):
        """
        是否包含数字
        :param lines:
        :return:
        """
        P_DIGIT = re.compile(u'\d+')
        digit = P_DIGIT.findall(content)
        if digit:
            logger.error("{}\t contains numbers is {}\t{}".format(self.filepath, digit, content))

    def is_have_symbol(self, content):
        """
        判断是否有特殊字符
        :param lines: 行内容
        :return:
        """
        P_SYMBOL_FULL = re.compile(self.err_symbol)
        special_symbol = P_SYMBOL_FULL.findall(content)
        if special_symbol:
            logger.error("{}\t contains special symbol is {}\t {}".format(self.filepath, special_symbol, content))

    def check(self, lines=None):
        # 检查单行多行
        if not lines:
            lines = self.read_file()
        self.is_one_line(lines)

        content = "".join(lines).strip()
        self.is_have_digit(content)  # 检查数字
        self.is_double_str(content)  # 检查全角字符

        self.check_out(content, self.filepath)  # 检查正常噪音符号外的其他符号
        self.check_in(content, self.filepath)  # 检查噪音符号内的噪音符号（噪音符号嵌套问题）
        self.check_noisy(content, self.filepath)  # 检查没有标注噪音符号的噪音单词


class Metadata(File):
    def check(self):
        z = re.compile(u'[\u4e00-\u9fa5]')
        meta_no_null = ['SEX', 'AGE', 'ACC', 'ACT', "BIR"]
        meta = {}

        lines = self.read_file()
        for line in lines:
            line = line.strip()
            if z.search(line) and 'ORS' not in line:
                logger.error("{}\t content contains chinese".format(self.filepath))

            if len(line.split('\t')) > 3:
                logger.error("{}\t content redundant TAB keys".format(self.filepath))
            elif len(line.split('\t')) == 3:
                if "LBR" in line or "LBO" in line:
                    pass
                else:
                    logger.error("{}\t content redundant TAB keys, {}".format(self.filepath, line.split('\t')[0]))
            elif len(line.split('\t')) == 1:
                if line.split('\t')[0] in meta_no_null:
                    logger.error("{}\t {} key is null".format(self.filepath, line.split('\t')[0]))
            else:
                key = line.split('\t')[0]
                valve = line.split('\t')[1]
                meta[key] = valve

        for m in meta_no_null:
            if m not in meta.keys():
                logger.error("{}\t {} key is null".format(self.filepath, m))
            else:
                if not meta['SEX'] in ['Male', 'Female']:
                    logger.error("{}\t value format is err".format(self.filepath))


class WAV(object):
    min_length = 15
    audio_channel = 1
    sample_width = 2
    framerate = [16000, 22050, 44100]
    silent_section = 0.05

    def __init__(self, file_path):
        self.filepath = file_path

    def silent_section_check(self):
        start, end, t_all = get_wav_start_end(self.filepath)
        after_slient_section = t_all - end
        if start < self.silent_section or after_slient_section < self.silent_section:
            logger.error("{}\tsilent section long error".format(self.filepath))

    def check(self):
        # 静音段检查
        self.silent_section_check()
        fsize = os.path.getsize(self.filepath)
        if fsize / float(1024) < self.min_length:
            logger.error("{}\t size error".format(self.filepath))
        else:
            with wave.open(self.filepath, 'rb') as f:
                if not f.getnchannels() == self.audio_channel:
                    logger.error("{}\t channel error".format(self.filepath))
                if f.getframerate() not in self.framerate:
                    logger.error("{}\t sample error".format(self.filepath))
                if f.getsampwidth() != self.sample_width:
                    logger.error("{}\t sample width error".format(self.filepath))


if __name__ == '__main__':
    # project_path = r"\\10.10.30.14\刘晓东\oracle_交付\apy161101028_g_351人意大利语手机采集语音数据\完整数据包_processed\data"
    # project_path = r"\\10.10.30.14\刘晓东\oracle_交付\apy161101028_r_215小时意大利语手机采集语音数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\刘晓东\oracle_交付\apy161101033_g_405人法语手机采集语音数据\data"
    # project_path = r"\\10.10.30.14\刘晓东\oracle_交付\apy161101033_r_232小时法语手机采集语音数据\data"
    # project_path = r"\\10.10.30.14\刘晓东\oracle_交付\apy161101034_g_343人西班牙语手机采集语音数据\data"
    # project_path = r"\\10.10.30.14\刘晓东\oracle_交付\apy161101034_r_227小时西班牙语手机采集语音数据\data"
    # project_path = r"\\10.10.30.14\刘晓东\oracle_交付\apy170801048_338小时西班牙语手机采集语音数据\data"
    # project_path = r"\\10.10.30.14\刘晓东\oracle_交付\apy170901049_347小时意大利语手机采集语音数据\data"

    # project_path = r"\\10.10.30.14\格式整理_ming\apy161101022_r_235小时日语手机采集语音数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\格式整理_ming\APY161101029_r_292小时泰语手机采集语音数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\格式整理_ming\apy161101026_r_197小时韩语手机采集语音数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\格式整理_ming\APY161101027_g_351人德语手机采集语音数据_引导\完整数据包_加密后数据\data"

    project_path = r"\\10.10.30.14\apy161101014_g_132小时中文重口音手机采集语音数据\完整数据包_processed\data"
    # project_path = r"\\10.10.30.14\apy161101014_r_662小时中文重口音手机采集语音数据\完整数据包_processed\data"

    pc = ProjectCheck()
    pc.check(project_path)
