import os
import json
import requests
import datetime


def sign(school_id, password, auto_position, vaccine):
    # 获取 JSESSIONID
    school_id = school_id.strip()
    password = password.strip()
    vaccine = vaccine.strip()

    for retryCnt in range(3):
        try:
            url = 'http://ca.zucc.edu.cn/cas/login'
            params = {'service': 'http://yqdj.zucc.edu.cn/feiyan_api/h5/html/daka/daka.html'}
            r = requests.get(url, params, timeout=30)
            cookies = r.cookies.get_dict()
            data = {
                'authType': '0',
                'username': school_id,
                'password': password,
                'lt': '',
                'execution': 'e1s1',
                '_eventId': 'submit',
                'submit': '',
                'randomStr': ''
            }
            url = 'http://ca.zucc.edu.cn/cas/login;jsessionid=' + cookies['JSESSIONID']
            r = requests.post(url, data=data, params=params, cookies=cookies, allow_redirects=False, timeout=30)
            url = r.headers['Location']
            r = requests.get(url, allow_redirects=False, timeout=30)
            cookies = r.cookies.get_dict()
            break
        except Exception as e:
            print(e.__class__.__name__, end='\t')
            if retryCnt < 2:
                print("JSESSIONID 获取失败，正在重试")
            else:
                return "无法获取 JSESSIONID，请检查账号和密码"

    for retryCnt in range(3):
        try:
            # 获取问卷
            url = 'http://yqdj.zucc.edu.cn/feiyan_api/examen/examenSchemeController/findExamenSchemeById.do'
            r = requests.post(url, cookies=cookies, data={'esId': 2}, timeout=30)
            questions = json.loads(r.json()['data']['examen']['scheme'])['questions']

            # 填写表单并提交
            with open("./form.json", "r", encoding='utf-8') as f:
                form = json.load(f)
                if form['questions'] != questions:
                    return "打卡表单已更新，当前版本不可用"

                answer = form['answer']
                answer["填报日期(Date)"] = str(
                    datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8))).date())
                answer["自动定位(Automatic location)"] = auto_position
                answer["疫苗接种情况?(Vaccination status?)"] = vaccine
                data = json.dumps({"examenSchemeId": 2, "examenTitle": "师生报平安", "answer": answer})
                headers = {'Content-Type': 'application/json'}
                url = "http://yqdj.zucc.edu.cn/feiyan_api/examen/examenAnswerController/commitAnswer.do"
                r = requests.post(url, cookies=cookies, data=data, headers=headers, timeout=30)
                res = r.json()
                if res['code'] == 1000:
                    return '打卡成功'
                elif res['code'] == 14801:
                    return '今日已打卡'
                else:
                    return res['message']

        except Exception as e:
            print(e.__class__.__name__, end='\t')
            if retryCnt < 2:
                print("打卡失败，正在重试")
            else:
                return "打卡失败"


def wechatNotice(SCKey, message):
    print(message)
    url = 'https://sctapi.ftqq.com/{0}.send'.format(SCKey)
    print(url)
    data = {
        'title': message,
    }
    try:
        r = requests.post(url, data=data)
        if r.json()["data"]["error"] == 'SUCCESS':
            print("微信通知成功")
        else:
            print("微信通知失败")
    except Exception as e:
        print(e.__class__, "推送服务配置错误")


if __name__ == '__main__':
    msg = sign(os.environ["SCHOOL_ID"], os.environ["PASSWORD"], os.environ["AUTO_POSITION"], os.environ["VACCINE"])
    print(msg)
    if os.environ["SCKEY"] != '' and msg != '打卡成功':
        wechatNotice(os.environ["SCKEY"], msg)
