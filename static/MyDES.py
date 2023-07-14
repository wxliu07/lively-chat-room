import utils
import des_setting


class MyDes(object):
    def __init__(self):
        pass

    def _get_bit48_keys(self, encryption_key: str, is_encode=False) -> str:
        """
        通过明文密钥计算16个48bit得旋转子密码
        :param encryption_key: 明文密钥
        :param is_encode: 是否为加密
        :return: 16个48bit得旋转子密码
        """
        bit_64_key = utils.group_by_64_bit(encryption_key)[0][0]  # 计算64bit的密码
        bit_56_keys = self._spin_key(bit_64_key) if is_encode else self._spin_key(bit_64_key)[::-1]  # 16个56bit得旋转密码
        result = self._key_selection_replacement(bit_56_keys)  # 对56bit旋转密码进行压缩，得到追钟要用得16个48bit得子旋转密码
        current_status = "加密" if is_encode else "解密"
        # if des_setting.PRINT_KEY_IN_ENCODE is is_encode:
        #     if des_setting.IS_PRINT_BIT64_KEY:
        #         print(f"{current_status}过程中使用的密钥明文为{encryption_key}，对应的64bit的密钥：{bit_64_key}")
        #     if des_setting.IS_PRINT_16_BIT56_KEYS:
        #         print(f"{current_status}过程中的16个56bit的旋转子密钥")
        #         for bit_56_key in bit_56_keys:
        #             print(bit_56_key)
        #     if des_setting.IS_PRINT_16_BIT48_KEYS:
        #         print(f"{current_status}过程中的16个48bit的子密钥")
        #         for bit_48_key in result:
        #             print(bit_48_key)
        return result

    @staticmethod
    def _key_conversion(bit_64_key: str) -> str:
        """
        将64位原始密钥转换为56位的密钥，并进行一次置换
        :param bit_64_key: 64bit密钥
        :return: 56bit密钥
        """
        return utils.replace_block(bit_64_key, des_setting.CLEAR_CHECK_CODE)

    def _spin_key(self, bit_64_key: str) -> list:
        """
        计算所有的旋转获得子密钥
        :param bit_64_key: 64bit密钥
        :return: 计算16个56bit旋转子密钥
        """
        result = []
        kc = self._key_conversion(bit_64_key)  # 去除校验位
        first, second = kc[0: 28], kc[28: 56]
        # print(f"第{0}次旋转后的key： left: {first}, right: {second}")
        for i in range(16):
            first_after_spin = first[des_setting.LEFT_MOVE_COUNT[i]:] + first[:des_setting.LEFT_MOVE_COUNT[i]]
            second_after_spin = second[des_setting.LEFT_MOVE_COUNT[i]:] + second[:des_setting.LEFT_MOVE_COUNT[i]]
            # print(f"第{i + 1}次旋转后的key： left: {first_after_spin}, right: {second_after_spin}")
            result.append(first_after_spin + second_after_spin)
        return result

    @staticmethod
    def _key_selection_replacement(bit56_keys: str) -> list:
        """
        通过选择置换将56位得子密钥转化得到最终要用到的48位的子密钥
        :param bit56_keys: 56bit子密钥列表
        :return result: 48bit子密钥列表
        """
        bit48_keys = []
        for child_key56 in bit56_keys:
            bit48_keys.append(utils.replace_block(child_key56, des_setting.KEY_SELECT_BOX))
        return bit48_keys

    @staticmethod
    def _init_replace_block(bit_64block: str) -> str:
        """
        对一个块进行初态置换
        """
        return utils.replace_block(bit_64block, des_setting.IP)

    def _iteration(self, block: str, child_keys: str) -> str:
        """
        16轮迭代
        :param block:待加密的64位比特块
        :param child_keys: 16个48bit得旋转子密钥列表
        :return: 该块的加密结果
        """
        for i in range(16):
            left, right = block[0: 32], block[32: 64]  # 分成左右两个子块
            next_left = right  # 将这一轮原视的Right作为下一轮的Left
            f_result = self._f_function(right, child_keys[i])  # f函数
            right = utils.xor(left, f_result)  # # f函数的输出与left做异或得到下一轮的right
            # 拼接，准备进行下一轮
            block = next_left + right
        return block[32:] + block[:32]

    def _f_function(self, right: str, child_key: str):
        """
        f函数
        :param right:右32bit块
        :param child_key: 当前迭代次数对应的48bit旋转子密钥
        :return:
        """
        right_block48 = self._e_block_extend(right)  # E拓展置换
        key_xor_right = utils.xor(right_block48, child_key)  # 与子密钥key做异或
        sbc_result = self._s_box_compression(key_xor_right)  # S盒压缩置换
        return self._p_box_replacement(sbc_result)  # P盒置换

    @staticmethod
    def _e_block_extend(block: str) -> str:
        """
        E盒拓展置换
        :param block:32位比特块
        :return: 48比特的扩展块
        """
        extended_block = ""
        for i in des_setting.E_BOX:
            extended_block += block[i - 1]
        return extended_block

    @staticmethod
    def _s_box_compression(block48: str) -> str:
        """
        S盒置换，将48位的输入转换为32位输出
        """
        result = ""
        for i in range(8):
            row_bit = (block48[i * 6] + block48[i * 6 + 5]).encode(des_setting.DEFAULT_ENCODING)  # a_1,a_6
            line_bit = (block48[i * 6 + 1: i * 6 + 5]).encode(des_setting.DEFAULT_ENCODING)  # a_2,a_3,a_4,a_5
            decimal_row = int(row_bit, 2)  # 行
            decimal_line = int(line_bit, 2)  # 列
            data = des_setting.S_BOX[i][decimal_row][decimal_line]  # 压缩对应的十进制
            no_full = str(bin(data))[2:]  # 转化为二进制，但是还没有填充到4位
            while len(no_full) < 4:  # 对压缩的值进行扩充，使值长度位4
                no_full = des_setting.FILL_CHAR + no_full
            result += no_full
        return result

    @staticmethod
    def _p_box_replacement(block32: str) -> str:
        """
        P盒置换
        Return:
            返回经过P盒置换后的32位01串
        """
        return utils.replace_block(block32, des_setting.P_BOX)

    @staticmethod
    def _end_replace_block(block: str) -> str:
        """
        对经过16轮迭代后得到得64bit块进行终态转换
        :param block: 经过16轮迭代后得到得64bit块
        :return: 经过加密后的64bit块
        """
        return utils.replace_block(block, des_setting.IP_1)

    def _encode_and_decode_public(self, bit_64_blocks: str, encryption_key: str, is_encode: bool = True) -> str:
        """
        加密&解密の公共部分
        :param bit_64_blocks: 64bit块数组
        :param encryption_key: 密钥
        :param is_encode: 是否位加密，使用加密算法则位True，否则False
        :return: 返回经过最终转置得bit字符串且长度位64得整数倍
        """
        bit_48_keys = self._get_bit48_keys(encryption_key, is_encode)  # 通过明文密码计算得到16个48bit得旋转子密码

        result = ""
        for bit_64_block in bit_64_blocks:  # 分别对每个一64位长的bit字符串进行DES加密
            irb_result = self._init_replace_block(bit_64_block)  # 初始转置
            block_result = self._iteration(irb_result, bit_48_keys)  # 16轮迭代
            block_result = self._end_replace_block(block_result)  # 最终转置
            result += block_result
        return result

    def encode(self, plain_text: str, encryption_key: str) -> str:
        """
        DES加密算法
        :param plain_text:明文
        :param encryption_key:加密密钥
        :return:密文
        """
        blocks, encode_end_add_zeros_count = utils.group_by_64_bit(plain_text, False)  # 将输入的明文格式化为64个bit为一组的数组
        encode_cipher_text = self._encode_and_decode_public(blocks, encryption_key, True)  # 加密后的bit字符串密文
        return encode_cipher_text, encode_end_add_zeros_count  # 返回01密文和尾部追加得0得个数

    def decode(self, decode_cipher_text: str, decrypt_key: str, cut_zeros_count: int = 0) -> str:
        """
        DES解密算法
        :param cut_zeros_count: 明文钟填充得0得个数
        :param decode_cipher_text:密文
        :param decrypt_key: 解密密钥
        :return: 明文
        """
        blocks = utils.group_by_64_bit(decode_cipher_text, True)[0]  # 将比特字符串转化为64比特位单位得数组
        plaintext = self._encode_and_decode_public(blocks, decrypt_key, False)  # 解密后的bit字符串明文
        if cut_zeros_count > 0 and cut_zeros_count % 8 == 0:  # 判断是否要进行去0操作
            plaintext = plaintext[:-cut_zeros_count:]  # 从尾部去除对应得0
        if des_setting.IS_PRINT_RESULT_BY_64BIT:
            plain_text_by_array, add_full_in_end_count = utils.group_by_64_bit(plaintext, True)
            # print("解密得到的64bit字符串：")
            # for result_by_64bit_line in plain_text_by_array:
            #     print(result_by_64bit_line)
            # print(f"解密得到的64bit字符串【ps：去除填充的{des_setting.FILL_CHAR}】后：")
            if add_full_in_end_count > 0 and add_full_in_end_count % 8 == 0:
                plain_text_by_array[-1] = plain_text_by_array[-1][:-add_full_in_end_count:]
                # for result_by_64bit_line in plain_text_by_array:
                #     print(result_by_64bit_line)
        return utils.bit_decode(plaintext, des_setting.DEFAULT_ENCODING)  # 返回解码值

#
# if __name__ == '__main__':
#
#     des = MyDes()
#     text = input("明文=")
#
#     if des_setting.IS_PRINT_TEXT:
#         print(f"明文：{text}")
#
#     bit64_plain_text_str_array, end_add_zeros_count = utils.group_by_64_bit(text, False)
#     if des_setting.IS_PRINT_BIT64_PLAIN_TEXT_STR_ARRAY:
#         print("二进制明文(已使用默认得utf-8进行编码)：")
#         for line in bit64_plain_text_str_array:
#             print(line)
#         print(f"尾部填充了{end_add_zeros_count}个{des_setting.FILL_CHAR}")
#         if end_add_zeros_count > 0 and end_add_zeros_count % 8 == 0:
#             print(f"二进制明文(已使用默认得utf-8进行编码)【ps：去除填充得{des_setting.FILL_CHAR}后得明文编码结果为】：")
#             bit64_plain_text_str_array, end_add_zeros_count = utils.group_by_64_bit(text, False)
#             bit64_plain_text_str_array[-1] = bit64_plain_text_str_array[-1][:-end_add_zeros_count:]
#         for line in bit64_plain_text_str_array:
#             print(line)
#
#     key = input("密钥=")
#     if des_setting.IS_PRINT_KEY:
#         print(f"密钥：{key}")
#
#     cipher_text = des.encode(text, key)[0]
#     if des_setting.IS_PRINT_CIPHER_TEXT:
#         print(f"密文为：")
#         str_cipher_text = ""
#         for line in utils.group_by_64_bit(cipher_text, True)[0]:
#             print(line)
#             str_cipher_text += line
#
#     print(f"解密结果为：{des.decode(cipher_text, key, end_add_zeros_count)}")
