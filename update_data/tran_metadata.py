#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/5/8 14:29
# @Author  : yangmingming
# @Site    : 
# @File    : tran_metadata.py
# @Software: PyCharm
import os


class ConvertMetadata(object):

    def tran_new_mate(self, project_path):
        """
        处理成新metadata
        :param work_dir:
        :return:
        """
        sample_temp = """LHD	Datatang - v1.2
DBN	{DBN}
SES	{SES}
CMT	*** Speech Label Information ***
FIP	{DIR}
CCD	{CCD}
REP	{REP}
RED	{RED}
RET	{RET}
CMT	*** Speech Data Coding ***
SAM	{SAM}
SNB	{SNB}
SBF	{SBF}
SSB	{SSB}
QNT	{QNT}
NCH	{NCH}
CMT	*** Speaker Information ***
SCD	{SCD}
SEX	{SEX}
AGE	{AGE}
ACC	{ACC}
ACT	{ACT}
BIR	{BIR}
CMT	*** Recording Conditions ***
SNQ	{SNQ}
MIP	{MIP}
MIT	{MIT}
SCC	{SCC}
CMT	*** Label File Body ***
LBD	{LBD}
LBR	{LBR}
LBO	{LBO}
CMT	*** Customized Label Body ***
SRA	{SRA}
EMO	{EMO}
ORS	{ORS}
"""

        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith("metadata"):
                    file_path = os.path.join(root, file)
                    print(file_path)
                    meta = dict()
                    with open(file_path, 'r+', encoding='utf8')as f:
                        for line in f:
                            line_content = line.strip()
                            if line_content:
                                if len(line_content) == 3:
                                    meta[line_content] = ''
                                else:
                                    meta[line_content[:3]] = line_content[3:].strip()

                        lbr = meta.get("LBR")
                        if lbr:
                            meta["LBR"] = lbr.split("\t")[-1]
                        else:
                            meta["LBR"] = ''
                        dir = meta.get("DIR")
                        if not dir:
                            meta["DIR"] = meta.get("FIP")
                        sra = meta.get("SRA")
                        if not sra:
                            meta["SRA"] = ''
                        emo = meta.get("EMO")
                        if not emo:
                            meta["EMO"] = ''
                        new_content = sample_temp.format(**meta)
                        print(new_content)
                        # f.seek(0)
                        # f.truncate()
                        # f.write(new_content)

    def run(self):
        """
        控制逻辑
        :return:
        """

        # project_path = r"\\10.10.30.14\格式整理_ming\apy161101026_r_197小时韩语手机采集语音数据_朗读\完整数据包_加密后数据\data"
        project_path = r"\\10.10.30.14\apy161101014_g_132小时中文重口音手机采集语音数据\完整数据包_processed\data"
        self.tran_new_mate(project_path)


if __name__ == '__main__':
    cm = ConvertMetadata()
    cm.run()
