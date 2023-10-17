# coding=utf-8
import os
import requests
import time
import re

# CONFIG PART =====================================
uid = os.environ["UID"]
password = os.environ["PASSWORD"]
SendKey = os.environ["SENDKEY"]
minSpeed = float(os.environ["MINSPEED"])
minMileage = int(os.environ["MINMILEAGE"])

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'Host': 'jhc.sunnysport.org.cn',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'Origin': 'http://jhc.sunnysport.org.cn',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Referer': 'http://jhc.sunnysport.org.cn/login/',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}


def spawn_data(user_name, user_pwd, vrf):
    return {
        'username': user_name,
        'vrf': vrf,
        'password': user_pwd,
        "userType": "person",
        "agency": "体育部"
    }


def get_mid_text(text, start_str, end_str):
    start_index = text.index(start_str)
    if start_index >= 0:
        start_index += len(start_str)
    end_index = text.index(end_str)
    return text[start_index:end_index]


if __name__ == '__main__':
    session = requests.session()
    res = session.get("http://jhc.sunnysport.org.cn/login/", data={}, headers=header)
    header['Cookie'] = res.headers['Set-Cookie'].split(";")[0]
    html = res.text
    vrf = re.search('name="vrf" value="(.*?)">', html).group(1)
    data = spawn_data(uid, password, vrf)
    res = session.post('http://jhc.sunnysport.org.cn/login/', headers=header, data=data, allow_redirects=False)
    response_header = res.headers
    session_id = response_header['set-cookie'].split(";")[0]
    header['Cookie'] = session_id
    
    # 拿数据
    totalRecord = session.get('http://jhc.sunnysport.org.cn/runner/data/speed.json',headers=header).json()
    print(totalRecord)

    # 因为懒得写正则 所以目前的有效次数和有效里程都是从总的数据里直接算的
    totalMileage = 0
    validMileage = 0
    totalTimes = 0
    validTimes = 0

    todayRecord = {}
    if time.strftime("%Y-%m-%d", time.localtime()) in totalRecord[len(totalRecord)-1]['runnerTime']:
        todayRecord = totalRecord[len(totalRecord)-1]
        for dayRecord in totalRecord:
            totalMileage += dayRecord['runnerMileage']
            totalTimes += 1
            if dayRecord['runnerSpeed'] > minSpeed and dayRecord['runnerMileage'] > minMileage:
                validMileage += dayRecord['runnerMileage']
                validTimes += 1

    if todayRecord:
        desp = '今日跑步距离：{}\n\n今日跑步速度：{}\n\n---\n\n'.format(todayRecord['runnerMileage'],round(todayRecord['runnerSpeed'],2))
        desp += '总里程：{}\n\n总次数：{}\n\n---\n\n'.format(totalMileage,totalTimes)
        desp += '有效里程：{}\n\n有效次数：{}\n\n---\n\n'.format(validMileage,validTimes)
        print(desp)
        # 推数据
        msg2send = {
            'title': '阳光长跑记录已更新',
            'desp': desp
        }
        requests.post('https://sctapi.ftqq.com/{}.send'.format(SendKey),data=msg2send)


