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
from multiprocessing import Pool

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
                if suffix in [".txt", ".metadata", ".wav"]:
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

        if len(all_name_list) != len(set(all_name_list)):
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
        self.custom_leg_symbol = []
        # 获取特殊字符
        with open("err_symbol.txt", 'r', encoding='utf8')as f:
            self.err_symbol = f.read()

            # 将用户认为合法的字符剔除错误字符检验
            for single_char in self.custom_leg_symbol:
                self.err_symbol = self.err_symbol.replace(single_char, "")

        # 定义合法噪音符号
        self.noisy_list = ['[[lipsmack]]', '[[cough]]', '[[sneeze]]', '[[breath]]', '[[background]]', '[[laugh]]']
        # self.noisy_list = ["<NON>", "<SPK>", "<NPS>"]
        # self.noisy_list = ['[p]', '[n]', '[s]', '[t]', '[z]', '[h]', '[k]', '[r]', '[b]', '[a]', '[m]', '[n]']
        # self.noisy_list.extend(['[P]', '[N]', '[S]', '[T]', '[A]', '[B]', '[C]', '[D]'])

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

    def check_in(self, input_str, line_number):
        input_str = self.remove_noisy(input_str)
        res1 = re.findall('\\[\\(\\(.*?\\)\\)\\]', input_str)
        pattern = self.err_symbol
        if len(res1) > 0:
            for each in res1:
                new_str = each[3:-3]
                new_str = self.remove_noisy(new_str)
                special_symbol = re.findall(pattern, new_str)
                if special_symbol:
                    logger.error(f'{self.filepath}\tin contain symbol {special_symbol}\t{input_str}\t{line_number}')

        res2 = re.findall('\\[\\/.*?\\/\\]', input_str)
        if len(res2) > 0:
            for each in res2:
                new_str = each[2:-2]
                new_str = self.remove_noisy(new_str)
                special_symbol = re.findall(pattern, new_str)
                if special_symbol:
                    logger.error(f'{self.filepath}\tin contain symbol {special_symbol}\t{input_str}')

    def check_out(self, input_str, line_number):
        # 先去掉所有噪音符号
        new_str = self.remove_noisy(input_str)
        new_str = new_str.replace(f'[/', ' ').replace('/]', ' ').replace('[((', ' ').replace('))]', ' ')
        pattern = self.err_symbol
        special_symbol = re.findall(pattern, new_str)
        if special_symbol:
            logger.error(f'{self.filepath}\tout contain symbol {special_symbol}\t{input_str}\t{line_number}')

    def check_noisy(self, input_str, line_number):
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
                logger.error(f'{self.filepath}\tcontain other noisy {noisy_new}\t{input_str}\t{line_number}')

    def is_double_str(self, content, line_number):
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
            logger.error(
                "{}\t Has double str(quan jiao) is {}\t{}\t{}".format(self.filepath, double_s, content, line_number))

    def is_one_line(self, lines):
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

    def is_have_digit(self, content, line_number):
        """
        是否包含数字
        :param lines:
        :return:
        """
        P_DIGIT = re.compile(u'\d+')
        digit = P_DIGIT.findall(content)
        if digit:
            logger.error("{}\t contains the number {}\t{}\t{}".format(self.filepath, digit, content, line_number))

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

    def check(self, multi_line=False):
        """
        文本检查
        :param multi_line:  多行标志 默认单行
        :return:
        """

        def check_content(content, line_number=1):
            """
            内容检查
            :param content:  需要检查的内容
            :param index:   多行的情况，检查每一行，的行号
            :return:
            """
            self.is_have_digit(content, line_number)  # 检查数字
            self.is_double_str(content, line_number)  # 检查全角字符

            self.check_out(content, line_number)  # 检查正常噪音符号外的其他符号
            self.check_in(content, line_number)  # 检查噪音符号内的噪音符号（噪音符号嵌套问题）
            self.check_noisy(content, line_number)  # 检查没有标注噪音符号的噪音单词

        lines = self.read_file()  # 读取文件
        if multi_line:  # 多行的情况
            for line_index, line_content in enumerate(lines):
                line_number = line_index + 1
                line_content = line_content.strip().split("\t")[-1]
                check_content(line_content, line_number)
        else:  # 单行的情况
            self.is_one_line(lines)  # 检查是否为单行
            content = "".join(lines).strip().split("\t")[0]  # 将内容拼接检查其他内容
            check_content(content)


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
                    logger.error("{}\t {} value is null".format(self.filepath, line.split('\t')[0]))
                key = line.split('\t')[0]
                valve = ''
                meta[key] = valve
            else:
                key = line.split('\t')[0]
                valve = line.split('\t')[1]
                meta[key] = valve

        for m in meta_no_null:
            if m not in meta.keys():
                logger.error("{}\t {} key is null".format(self.filepath, m))

        if meta.get("SEX"):
            if meta.get("SEX") not in ['Male', 'Female']:
                logger.error("{}\t sex value format is err".format(self.filepath))


class WAV(object):
    min_length = 15
    audio_channel = 1
    sample_width = 2
    framerate = [16000, 22050, 44100, 48000]
    # framerate = [16000, 22050]
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

    # project_path = r"\\10.10.30.14\格式整理_ming\APY161101029_r_292小时泰语手机采集语音数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\格式整理_ming\apy161101022_r_235小时日语手机采集语音数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\apy161101014_r_662小时中文重口音手机采集语音数据\完整数据包_processed\data"
    # project_path = r"\\10.10.30.14\apy161101014_g_132小时中文重口音手机采集语音数据\完整数据包_processed\data"

    # project_path = r"\\10.10.30.14\格式整理_ming\apy161101026_r_197小时韩语手机采集语音数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\格式整理_ming\APY161101027_g_351人德语手机采集语音数据_引导\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\apy180901052_287小时日语手机采集语音数据\完整数据包_processed\data"
    # project_path = r"\\10.10.30.14\apy161101013_1505小时普通话手机采集语音数据\完整数据包_加密后数据\data"

    # project_path = r"\\10.10.30.14\格式整理_ming\apy161101027_r_211小时德语手机语音采集数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\格式整理_ming\apy161101010_593小时中国人说英语手机采集语音数据\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\格式整理_ming\apy161101028_r_215小时意大利语手机采集语音数据_朗读\完整数据包_加密后数据\data"

    # project_path = r"\\10.10.30.14\刘晓东\数据分类\语音数据\apy161101032_g_357人英式英语手机采集语音数据\完整数据包_processed\data"
    # project_path = r"\\10.10.30.14\刘晓东\数据分类\语音数据\apy161101032_r_199小时英式英语手机采集语音数据\完整数据包_processed\data"
    # project_path = r"\\10.10.30.14\apy161101005_245小时车载环境普通话手机采集语音数据\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\格式整理_ming\APY161101044_r_156人马来西亚语手机采集数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\apy161101007_250人苏州方言手机采集语音数据2\完整数据包_加密后数据\data"

    # project_path = r"\\10.10.30.14\刘晓东\数据分类\语音数据\apy161101030_g_496人印尼语手机采集语音数据\完整数据包_processed\data"
    # project_path = r"\\10.10.30.14\apy170501037_1297小时录音笔采集场景噪音数据\完整数据包_processed\data"
    # project_path = r"\\10.10.30.14\apy161101004_101小时录音笔采集场景噪音数据\完整数据包_加密后数据\data"

    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101040_1420小时普通话自然语音手机采集数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101021_r_1032小时上海方言手机采集语音数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101020_r_1652小时粤语手机采集语音数据_朗读\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101019_r_794小时四川方言手机采集语音数据_朗读\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\格式整理_ming\apy161101018_r_1044小时闽南语手机采集语音数据_朗读\完整数据包_加密后数据\data"

    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101010_593小时中国人说英语手机采集语音数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101003_3125小时语音助手普通话实网采集语音数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101002_1175小时语音助手普通话实网采集语音数据\完整数据包_加密后数据\data\category"

    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101001_140小时电商客服普通话实网采集语音数据\完整数据包_加密后数据\data\category\G0001"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101043_g_203人台湾普通话手机采集数据\完整数据包_processed\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101045_797人低幼儿童麦克风手机采集语音数据\完整数据包_processed\data\categoryPhone"
    # project_path = r"\\10.10.30.14\语音数据_2016\APY161101043_R_204人台湾普通话手机采集数据\完整数据包\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101016_463人河南方言手机采集语音数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101008_370人杭州方言手机采集语音数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101007_250人苏州方言手机采集语音数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101039_220人美国儿童麦克风采集语音数据_朗读\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101023_201人英国儿童麦克风采集语音数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2017\apy170101041_531小时麦克风手机采集车载噪音数据\完整数据包_加密后数据\data"
    # project_path = r"\\10.10.30.14\语音数据_2017\APY170701046_1_849小时普通话家居交互手机语音数据（998人远场家居采集语音数据子集）\完整数据包_processed"
    # project_path = r"\\10.10.30.14\语音数据_2017\APY171101050_2_118人数字方言普通话手机采集语音数据\完整数据包_ming\data"
    # project_path = r"\\10.10.30.14\语音数据_2017\APY171101050_1_474人数字方言普通话手机采集语音数据\完整数据包_ming\data"
    # project_path = r"\\10.10.30.14\语音数据_2017\apy170401036_s_200人中文手机采集语音数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101024_r_203人噪音环境口音普通话手机采集语音数据_朗读\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101024_g_205人噪音环境口音普通话手机采集语音数据\完整数据包_processed\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2017\apy170401036_w_200人中文唤醒词手机语音采集数据\完整数据包_processed\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2017\APY170801047_35小时有声读物文本拼音标注语音数据\完整数据包\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2017\apy170501038_20人英文情感语音麦克风采集数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101017_312人东北方言手机采集语音数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101015_r_738小时维语手机采集语音数据_朗读\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101006_754人外国人说汉语手机采集语音数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101005_245小时车载环境普通话手机采集语音数据\完整数据包_加密后数据\data\category"
    # project_path = r"\\10.10.30.14\语音数据_2016\apy161101025_739人中国儿童麦克风采集语音数据\完整数据包_processed\data\category"
    project_path = r"\\10.10.30.14\语音数据_2016\APY161101043_R_204人台湾普通话手机采集数据_朗读\完整数据包_加密后数据\data\category"

    pc = ProjectCheck()
    # pc.check_file_complete(project_path)  # 检查文件的完整性
    pc.check(project_path)
