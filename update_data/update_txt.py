import os


class TXT(File):
    def ch_to_en(self, lines):
        # 中文标点转英文
        table = {ord(f):ord(t) for f,t in zip('【】；‘’：“”《》，。、？','[];\'\':""<>,. ?')}
        return [text.translate(table) for text in lines]

    def is_double_str(self, lines):
        # 是否包含全角
        double_str = lambda x: ord(x) == 0x3000 or 0xFF01 <= ord(x) <= 0xFF5E
        for line in lines:
            for x in line:
                if double_str(x):
                    self.flag = False
                    logger.error("Has double str(quan jiao) {}".format(self.filepath))
                    return

    def dbc2sbc(self, lines):
        # ' 全角转半角'
        new_lines = []
        for line in lines:
            rstring = ''
            for uchar in line:
                inside_code = ord(uchar)
                if inside_code == 0x3000:
                    inside_code = 0x0020
                else:
                    inside_code -= 0xfee0
                if not (0x0021 <= inside_code and inside_code <= 0x7e):
                    rstring += uchar
                    continue
                rstring += chr(inside_code)
            new_lines.append(rstring)
        return new_lines


class File:
    GROUP_REGEX = re.compile('(?P<group>[G|Z]\d+)[A-F\d_]*(?P<session>S\d+)\.')

    def __init__(self, filepath):
        self.filepath = filepath
        self.flag = True
        r = self.GROUP_REGEX.search(os.path.basename(filepath))
        if r:
            self.group = r.group('group').strip()
        else:
            self.group = os.path.basename(filepath)

    def read_file(self):
        # 是否utf-8编码
        try:
            f = open(self.filepath, 'r', encoding='utf-8')
            return f.readlines()
        except UnicodeDecodeError as e:
            logger.error("{} not encode utf-8".format(self.filepath))
            self.flag =False
            return ['']

    def is_has_ch(self, lines):
        # 是否含有中文
        z = re.compile(u'[\u4e00-\u9fa5]')
        for line in lines:
            if z.search(line):
                self.flag = False
                logger.error("Has chinese in {}".format(self.filepath))
                return

    def write_file(self, lines):
        with open(self.filepath, 'w') as f:
            for line in lines:
                f.write(line)




