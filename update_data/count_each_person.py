import os
from pydub import AudioSegment
import pandas as pd
import logging
logger = logging.getLogger("YMM")
log_path = os.getcwd() + '/Logs/'
n = 1
log_name =log_path+'//'+str(n) + '-log.log'
if not os.path.exists(log_path):
    os.makedirs(log_path)

while os.path.exists(log_name):
    n += 1
    log_name = log_path + str(n) + '-log.log'
fh = logging.FileHandler(log_name, mode='a', encoding="utf8")
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
logger.addHandler(fh)
logger.addHandler(console)

def get_person_sum(wav_list):
    s = 0
    for wav_path in wav_list:
        t = get_wav_durtion(wav_path)
        s += t
    return s


# 获取以suffix为后缀的文件路径列表
def get_file_list(input_dir, suffix):
    file_list = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(suffix):
                path = root + '\\' + file
                file_list.append(path)
    return file_list


def get_meta_dict(meta_path):
    metadata_dict = {}
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                l_list = line.split('\t')
                if len(l_list) > 1:
                    metadata_dict[l_list[0]] = l_list[1].strip()
                elif len(l_list) == 1:
                    metadata_dict[l_list[0]] = ''
    except Exception as e:
        print('err：' + meta_path)
    return metadata_dict


def get_wav_durtion(wav_path):
    sound = AudioSegment.from_file(wav_path)
    # 获取文件时长
    sound_time = sound.duration_seconds
    return sound_time


def get_dir_list(work_dir):
    dir_list = []
    for dir in os.listdir(work_dir):
        path = work_dir + '\\' + dir
        if os.path.isdir(path):
            dir_list.append(path)
    return dir_list

def check_person_info(wav_list):
    """
    检查一个人的meta信息是否一致
    :param wav_file_list:
    :return:
    """
    info_set = set()
    meta_dict = get_meta_dict(wav_list[0].replace('.wav', '.metadata'))
    sex = meta_dict['SEX']
    age = meta_dict['AGE']
    acc = meta_dict['ACC']
    act = meta_dict['ACT']
    bir = meta_dict['BIR']
    mit = meta_dict['MIT']
    first_info = (sex, age, acc, act, bir, mit)

    for wav_file in wav_list:
        meta_path = wav_file.replace('.wav', '.metadata')
        meta_dict = get_meta_dict(meta_path)
        sex = meta_dict['SEX']
        age = meta_dict['AGE']
        acc = meta_dict['ACC']
        act = meta_dict['ACT']
        bir = meta_dict['BIR']
        mit = meta_dict['MIT']
        info = (sex, age, acc, act, bir, mit)
        info_set.add(info)
        if not first_info == info:
            logger.error(meta_path+'\t'+str(info)+'\tfirst:'+str(first_info))
    return first_info


if __name__ == '__main__':
    # work_dir = r'\\10.10.30.14\刘晓东\oracle_交付\apy161101034_r_227小时西班牙语手机采集语音数据\data\category'
    # res_path = r'\\10.10.30.14\刘晓东\oracle_交付\apy161101034_r_227小时西班牙语手机采集语音数据\apy161101034_r_227小时西班牙语手机采集语音数据.xlsx'
    # work_dir = r'\\10.10.30.14\刘晓东\oracle_交付\apy170801048_338小时西班牙语手机采集语音数据\data\category'
    # res_path = r'\\10.10.30.14\刘晓东\oracle_交付\apy170801048_338小时西班牙语手机采集语音数据\apy161101034_r_227小时西班牙语手机采集语音数据.xlsx'

    # work_dir = r"\\10.10.30.14\刘晓东\数据分类\语音数据\apy161101032_r_199小时英式英语手机采集语音数据\完整数据包_processed\data\category"
    # res_path = r'\\10.10.30.14\刘晓东\数据分类\语音数据\apy161101032_r_199小时英式英语手机采集语音数据\apy161101032_r_199小时英式英语手机采集语音数据.xlsx'

    # work_dir = r"\\10.10.30.14\刘晓东\数据分类\语音数据\apy161101032_r_199小时英式英语手机采集语音数据\完整数据包_processed\data\category"
    # res_path = r'\\10.10.30.14\刘晓东\数据分类\语音数据\apy161101032_r_199小时英式英语手机采集语音数据\apy161101032_r_199小时英式英语手机采集语音数据.xlsx'
    # work_dir = r"\\10.10.30.14\刘晓东\数据分类\语音数据\apy161101032_g_357人英式英语手机采集语音数据\完整数据包_processed\data\category"
    # res_path = r'\\10.10.30.14\刘晓东\数据分类\语音数据\apy161101032_g_357人英式英语手机采集语音数据\apy161101032_g_357人英式英语手机采集语音数据.xlsx'
    # work_dir = r"\\10.10.30.14\apy161101005_245小时车载环境普通话手机采集语音数据\完整数据包_加密后数据\data\category"
    # res_path = r'\\10.10.30.14\apy161101005_245小时车载环境普通话手机采集语音数据\apy161101005_245小时车载环境普通话手机采集语音数据.xlsx'

    work_dir = r"\\10.10.30.14\apy161101014_r_662小时中文重口音手机采集语音数据\完整数据包_processed\data\category"
    res_path = r'\\10.10.30.14\apy161101014_r_662小时中文重口音手机采集语音数据\apy161101014_r_662小时中文重口音手机采集语音数据.xlsx'

    print(work_dir)

    data = []
    for person in get_dir_list(work_dir):
        try:
            name = person.split('\\')[-1]
            wav_list = get_file_list(person, '.wav')
            info = check_person_info(wav_list)
            wav_sum = get_person_sum(wav_list)
            person_info = [name, *info,wav_sum]
            data.append(person_info)
        except Exception as e:
            logger.error(person+'\t'+'other_error'+'\t'+str(e))

    df = pd.DataFrame(data, columns=['person_num', 'SEX', 'AGE', 'ACC', 'ACT', 'BIR', 'MIT','wav_durtion'])
    df.to_excel(res_path, index=False)