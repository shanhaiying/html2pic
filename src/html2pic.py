# coding:utf-8
"""html 转图片主程序"""
import config
from mathexpress import findmath
from selenium import webdriver
from PIL import Image
import os
import time
import codecs
import hashlib


def _generate_valid_html(math_express, css_path=None):
    """将匹配成功的代码添加标签"""
    if css_path is None:
        css_path = u'style.css'
    return u"""<html> <head><link rel="stylesheet" type="text/css"
    href="{css_path}"></head><body><div id="replace_div"><span
    id='replace_span'>{math_express}</span></div>
    </body></html>""".format(math_express=math_express, css_path=css_path)


def _save_valid_html(html):
    valid_html = _generate_valid_html(html)
    filename = str(long(time.time() * 10000)) + '.html'
    file_path = os.path.join(config.html_save_tmp_path, filename)
    with codecs.open(filename=file_path, mode='wb', encoding='utf-8') as f:
        f.write(valid_html)
    return file_path


def _delete_file(file_path):
    try:
        os.remove(file_path)
    except Exception:
        pass


def _crop(div, span, screenshot_path, png_name):
    """截图 这儿通过传入一个span获得需要截取部分的长度,传入一个div获得
    对象的高度来保证在截图时不会截取过长同时又不会纵向截取缺失"""
    img = Image.open(screenshot_path)
    left = int(div.location['x'])
    top = int(div.location['y'])
    right = left + span.size['width']
    bottom = top + div.size['height']
    window = (left, top, right, bottom)
    region = img.crop(window)
    png_path = os.path.join(config.png_path, png_name)
    region.save(png_path)
    return png_path


def _exists_png(png_name):
    """在配置目录下是否已存在对应图片"""
    if png_name in set(os.listdir(config.png_path)):
        return True
    else:
        return False


def _draw(driver, html):
    """传入的html代码进行截图"""
    png_name = u"%s.png" % hashlib.md5(html.encode('utf-8')).hexdigest()
    if _exists_png(png_name):
        # print("=="*10 + "exists: " + png_name + "=="*10)
        return png_name
    html_path = _save_valid_html(html)
    url = "file://" + html_path
    driver.get(url)
    div = driver.find_element_by_xpath('//*[@id="replace_div"]')
    span = driver.find_element_by_xpath('//*[@id="replace_span"]')
    screenshot_name = str(long(time.time() * 10000)) + '.png'
    screenshot_path = os.path.join(config.screenshot_path, screenshot_name)
    driver.save_screenshot(screenshot_path)
    png_path = _crop(div=div, span=span, screenshot_path=screenshot_path, png_name=png_name)
    # 删除生成的临时文件
    _delete_file(html_path)
    _delete_file(screenshot_path)
    return png_path


def _replace_start(data_str, src_str, des_str=u''):
    if data_str.startswith(src_str):
        return des_str + data_str[len(src_str):]
    return data_str


def html2pic(rules_path, html_path=None, html_content=None, driver=None):
    """
        rules_path: 规则文件路径
        html_path: 需要转图片的html文件路径
        html_content:需要转图片的html文本内容，在没有提供html_path的时候启用
        return: 返回一组相关源码和源码存储的图片地址
    """
    if driver is None:
        driver = webdriver.Chrome()
    match_htmls = findmath(rules_path, html_path, html_content)
    html2pics = dict()
    for html in match_htmls:
        cdriver = None
        if check_contain_chinese(html):
            if driver is None or not isinstance(driver, webdriver.Chrome):
                cdriver = webdriver.Chrome()
                driver = cdriver
        else:
            continue
        html2pics.update({html: _draw(driver, html)})
        if cdriver is not None:
            cdriver.close()
    return html2pics

def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            print check_str
            return True
    return False

def test_from_db():
    import MySQLdb
    db = MySQLdb.connect(**config.mysql_config)
    cursor = db.cursor()
    cursor.execute(
        """select option_a,option_b,option_c,option_d,title,parse,answer1,
        answer2 from questions where subjectId=9""")
    data_list = cursor.fetchall()
    driver = webdriver.PhantomJS()
    driver = webdriver.Chrome()
    results = list()
    start = time.time()
    count = 0
    for data in data_list:
        count += 1
        if count % 101:
           print count
        for item in data:
            if item is None or len(item) == 0:
                pass
            else:
                try:
                    result = html2pic("/Users/lovechenao/gitroom/html2pic/"
                                  "src/okay/rules/chemistry.rule",
                                      html_content=item, driver=driver)
                    results.append(result)
                except Exception as e:
                    print e
    print len(results)
    print time.time() - start
    driver.close()


if __name__ == '__main__':
    # args = sys.argv
    # if len(args) != 3:
    #     print("""
    #    example: python html2pic rules_path html_path
    #    """)
    # driver = webdriver.Chrome()
    # try:
    #     print html2pic(rules_path=args[1], html_path=args[2], driver=driver)
    # except Exception as e:
    #     print e
    # driver.close()
    test_from_db()
