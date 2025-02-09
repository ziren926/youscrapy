def parse_cookie_string(cookie_string: str) -> str:
    """将cookie字符串转换为Netscape格式"""
    cookie_pairs = cookie_string.split(';')
    netscape_cookies = []

    for pair in cookie_pairs:
        if '=' in pair:
            name, value = pair.strip().split('=', 1)
            # Netscape 格式：domain	TRUE/FALSE	path	secure	expiry	name	value
            netscape_line = f".youtube.com\tTRUE\t/\tFALSE\t2147483647\t{name}\t{value}"
            netscape_cookies.append(netscape_line)

    # 添加必要的头部注释
    header = "# Netscape HTTP Cookie File\n# https://curl.haxx.se/rfc/cookie_spec.html\n# This is a generated file!  Do not edit.\n\n"
    return header + "\n".join(netscape_cookies)

def create_cookie_file(cookie_string: str, output_file: str = "youtube_cookies.txt"):
    """创建cookie文件"""
    netscape_format = parse_cookie_string(cookie_string)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(netscape_format)
    return output_file