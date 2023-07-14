import re
import setting


def bit_decode(s: str, rule: str = setting.DEFAULT_ENCODING) -> str:
    """
    将01字符串（不加任何标识符和纠错码）转化为对应的明文字符串（默认config.DEFAULT_ENCODING)
    :param rule: 解码规则
    :param s:01字符串
    :return:解码原文
    """
    if len(s) == 0:
        return '>>内容为空<<'
    if len(s) % 8 != 0:
        raise SyntaxError('编码不是八的倍数')  # 至少是字节的倍数才能操作
    msg = re.sub(r'0x', '', hex(int(s, 2)))
    rtn = bytes.fromhex(msg).decode(rule)
    return rtn


def bit_encode(s: str, rule: str = setting.DEFAULT_ENCODING) -> str:
    """
    将明文字符串按照rule的格式转化为01字符串
    :param s: 待编码字符串
    :param rule: 编码方案 默认config.DEFAULT_ENCODING
    :return: 字符串对应01字符串
    """
    bytes_array = s.encode(rule)  # 首先将字符串s编码，返回一个bytes类型bytes_array
    bin_str_array = [bin(int(i))[2:].rjust(8, '0') for i in bytes_array]  # bytes_array转二进制字符串数组（每个byte8个bit）
    return ''.join(bin_str_array)  # 拼接结果


def group_by_64_bit(enter: str, is_bit_string: bool = False) -> list:
    """
    将输入的字符串转换为二进制形式，并没64位为一组进行分割
    :param enter:要转换的字符串
    :param is_bit_string: 是否位bit字符串，如果是比特字符串，则填True，否则False
    :return: 64倍整数的字符串数组以及填充的数量
    """
    result = []
    add_zeros_count = 0
    bit_string = enter if is_bit_string else bit_encode(enter)
    # 如果长度不能被64整除，就填充
    if len(bit_string) % 64 != 0:
        for i in range(64 - len(bit_string) % 64):
            add_zeros_count += 1
            bit_string += setting.FILL_CHAR
    for i in range(len(bit_string) // 64):
        result.append(bit_string[i * 64: i * 64 + 64])
    # print(f"转换为二进制后的初始明文： {result}")
    return result, add_zeros_count


def replace_block(block: str, replace_table: tuple) -> str:
    """
    对单个块按照指定的转置表进行置换
    :param block: 要进行转换的64位长的01字符串
    :param replace_table: 转换表
    :return: 返回转换后的字符串
    """
    result = ""
    for i in replace_table:
        try:
            result += block[i - 1]
        except IndexError:
            # print(f"i={i}, block= {block}, len={len(block)}")
            raise
    return result


def xor(a: str, b: str) -> str:
    """
    对两个01字符串做异或
    """
    result = ""
    size = len(a) if len(a) < len(a) else len(b)
    for i in range(size):
        result += '0' if a[i] == b[i] else '1'
    return result


def bin_str_to_int(bin_str: str) -> int:
    """
    二进制字符串转化为十进制
    :param bin_str: 二进制字符串
    :return: 十进制数
    """
    length, result = len(bin_str), 0
    return sum([int(bin_str[index]) * 2 ** (length - 1 - index) for index in range(length)])


def int_to_bin_str(n: int, length: int = None) -> str:
    """
    十进制数字转化为二进制字符串
    :param length: 输出返回的长度规定
    :param n: 十进制数字
    :return: 二进制字符串
    """
    result = bin(n).replace('0b', '')
    if length is None or length <= result.__len__():
        return result
    else:
        return result.zfill(length)


if __name__ == '__main__':
    print(xor("010101", "111000"))
