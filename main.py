from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from bs4 import BeautifulSoup
import time
import datetime
from flask import Flask, render_template
from flask import request

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    return render_template('hello.html')

@app.route('/resultSet',methods=["GET","POST"])
def model():
    #从初始界面获取数据
    partition_nums = int(100.0/float(request.form['precision']))
    begin = int(request.form['begin'])
    end = int(request.form['end'])
    type = request.form['selectList']
    excel = request.form['excel']
    if(excel == '1'):
        excel_name=request.form['excelName']
        xlsWriter = pd.ExcelWriter(r"D:\%s.xls" % excel_name)

    #变量初始化
    thead = ["基金代码", "基金简称", "日期", "单位净值", "累计净值", "日增长率", "近1周", "近1月",
         "近3月", "近6月", "近1年", "近2年", "近3年", "今年来", "成立来", "自定义", "手续费"]
    all_rank = {}
    inc_map = {}
    inc = {}
    all_dict = {}
    select_dict = {}

    for i in range(begin, end):
        inc_map[i] = {}
        all_rank[i] = []
        inc[i] = []
        all_dict[i] = {}
        select_dict[i] = {}
        for j in range(len(thead)):
            all_dict[i][thead[j]] = []
            select_dict[i][thead[j]] = []

    #得到year这个年份的排名数据（排名越高，id在列表中越靠前）
    def getRank(url, year):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-browser-side-navigation')
        driver = webdriver.Chrome(options=chrome_options)
        # driver = webdriver.Chrome()
        driver.get(url)
        time.sleep(10)

        soup = BeautifulSoup(driver.page_source)
        dbtable = soup.findAll(name="table", attrs={"id": "dbtable"})

        trs_item = dbtable[0].tbody.findAll(name="tr")

        for tr_item in trs_item:
            tds = tr_item.findAll(name="td")
            all_rank[year].append(tds[2].text)

        if(excel == '1'):
            for tr_item in trs_item:
                tds = tr_item.findAll(name="td")
                for i in range(len(thead)):
                    all_dict[year][thead[i]].append(tds[i+2].text)

        #pd.DataFrame(all_dict).to_excel(excel_writer=xlsWriter, sheet_name=year, index=None)

        print("%s,nums=%d,%s" % (year, len(all_rank[year]), url))
        driver.close()

    #得到year这个年份每个id对应的涨幅数据
    def getInc(url, year):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-browser-side-navigation')
        driver = webdriver.Chrome(options=chrome_options)
        # driver = webdriver.Chrome()
        driver.get(url)
        # time.sleep(10)

        soup = BeautifulSoup(driver.page_source)
        dbtable = soup.findAll(name="table", attrs={"id": "dbtable"})

        trs_item = dbtable[0].tbody.findAll(name="tr")

        for tr_item in trs_item:
            ids = tr_item.findAll(name="td")
            l = len(ids[17].text)
            t_inc = ids[17].text[0:l - 1]
            if t_inc != "--":
                inc_map[year][ids[2].text] = float(t_inc)
        driver.close()

    # 得到当年基金排名
    for i in range(begin, end):
        beginDay = '%d0101' % i
        endDay = '%d1231' % i
        url_dict = {
            "all": "http://fund.eastmoney.com/data/fundranking.html#tall;c0;r;sqjzf;pn10000;ddesc;qsd%s;qed%s;qdii;zq;gg;gzbd;gzfs;bbzt;sfbb" % (
                beginDay, endDay),
            "gp": "http://fund.eastmoney.com/data/fundranking.html#tgp;c0;r;sqjzf;pn10000;ddesc;qsd%s;qed%s;qdii;zq;gg;gzbd;gzfs;bbzt;sfbb" % (
                beginDay, endDay),
            "hh": "http://fund.eastmoney.com/data/fundranking.html#thh;c0;r;sqjzf;pn10000;ddesc;qsd%s;qed%s;qdii;zq;gg;gzbd;gzfs;bbzt;sfbb" % (
                beginDay, endDay),
            "zq": "http://fund.eastmoney.com/data/fundranking.html#tzq;c0;r;sqjzf;pn10000;ddesc;qsd%s;qed%s;qdii;zq;gg;gzbd;gzfs;bbzt;sfbb" % (
                beginDay, endDay),
            "zs": "http://fund.eastmoney.com/data/fundranking.html#tzs;c0;r;sqjzf;pn10000;ddesc;qsd%s;qed%s;qdii;zq;gg;gzbd;gzfs;bbzt;sfbb" % (
                beginDay, endDay)
        }
        for key, url in url_dict.items():
             if key == type:
                getRank(url, i)

    # 得到所有年份所有排名的基金次年的业绩
    for i in range(begin, end):
        beginDay = '%d0101' % (i + 1)
        endDay = '%d1231' % (i + 1)
        url = "http://fund.eastmoney.com/data/fundranking.html#tgp;c0;r;sqjzf;pn10000;ddesc;qsd%s;qed%s;qdii;zq;gg;gzbd;gzfs;bbzt;sfbb" % (
        beginDay, endDay)
        print(i, url)
        getInc(url, i)

    #seg = request.form[seg]
    for year, rank in all_rank.items():
        print("len=", len(rank))
        l = len(rank) // partition_nums
        print("l=", l)
        for i in range(0, partition_nums):
            sum = 0.0
            empty = 0.0
            for j in range(0, l):
                print(i * l + j, ",", year)
                if rank[i * l + j] in inc_map[year].keys():
                    sum += inc_map[year][rank[i * l + j]]
                else:
                    empty += 1.0
            inc[year].append(sum * partition_nums / (partition_nums - empty))

    # 求所有年份对应排名第二年平均收益率，并求出最优区间
    inc_sum = []
    sum = 0.0
    for i in range(0, partition_nums):
        for j in range(begin, end):
            sum += inc[j][i]
        inc_sum.append(sum)
        inc_sum[i] /= partition_nums

    result_seg = int(request.form['result_seg'])
    max_seg = 0.0
    current_seg = 0.0
    seg_begin = 0
    seg_end = result_seg
    for i in range(0, result_seg):
        max_seg += inc_sum[i]
        current_seg += inc_sum[i]
    for i in range(0, 100 - result_seg):
        current_seg = current_seg - inc_sum[i] + inc_sum[i + result_seg]
        if current_seg > max_seg:
            seg_begin = i
            seg_end = i + result_seg

    #print("最优区间:", seg_begin, ' ', seg_end)
    #print("平均最优收益率:", max_seg)

    if(excel == '1'):
        for year, rank in all_rank.items():
            l = len(rank)//partition_nums
            for i in range(l * seg_begin, l * seg_end):
                for j in range(len(thead)):
                        select_dict[year][thead[j]].append(all_dict[year][thead[j]][i])
        pd.DataFrame(select_dict[year]).to_excel(excel_writer=xlsWriter, sheet_name=str(year), index=None)

    return render_template('Result.html',
                           seg_begin=seg_begin,
                           seg_end=seg_end,
                           max_seg=max_seg)

if __name__ == '__main__':
    app.run(debug=True)
