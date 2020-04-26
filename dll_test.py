import os

from pydub import AudioSegment

exe = r'wav_5_9.exe'


def cmd_run(filename):
    cmd = exe + ' 2 ' + filename
    result = os.popen(cmd).readline()
    return result.split(': ')[-1].strip()


def get_wav_durtion(wav_path):
    sound = AudioSegment.from_file(wav_path)
    # 获取文件时长
    sound_time = sound.duration_seconds
    return sound_time


def main():
    work_list = []
    work_list.append(r'\\10.10.30.14\李昺3\数据整理\已完毕\语音类\格式整理_ming\apy161101030_r_360小时印尼语手机采集语音数据_朗读\完整数据包_加密后数据\data')
    sum = 0
    a = 0
    with open('360小时印尼语手机.txt', 'w', encoding='utf-8') as f:
        for work in work_list:
            print(work)
            for root, dirs, files in os.walk(work):
                for file in files:
                    if file.endswith('wav'):
                        wav_path = root + '\\' + file
                        res = cmd_run(wav_path)
                        # print(wav_path,res)
                        if res == '5':
                            a += 1
                            t = get_wav_durtion(wav_path)
                            sum += t
                            f.write(wav_path + '\n')
    print('切音文件数量：',a)
    print(sum / 3600, 'hours')


if __name__ == '__main__':
    main()
