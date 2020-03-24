# -*- coding: utf-8 -*-
import json
import urllib.parse
import requests
import datetime
import slack
import time
import os
from operator import itemgetter

CONFFILE = os.path.dirname(__file__) + '/config.json'
DEFAULT_PERIOD_DAYS = 60
DEFAULT_ABSENCE_DAYS = 7

DT0 = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

def getQueryString(params):
    param_array = []
    for k in params:
        param_array.append(urllib.parse.quote(k) + '=' + urllib.parse.quote(params[k]))
    return '&'.join(param_array)

def fetchStudentRecords(domain, id, api_token):
    # kintone から在籍中の生徒一覧を取得
    limit = 500
    headers = {"X-Cybozu-API-Token": api_token}
    base_query = '(StartDate  <= TODAY() ) and (' \
                + '(Course  in ("6ヶ月コース") and StartDate >= FROM_TODAY(-365, DAYS)) or ' \
                + '(Course  in ("3ヶ月コース") and StartDate >= FROM_TODAY(-92, DAYS)))'
    offset = 0
    totalcount = 0
    records = []
    while True:
        params_array = {
            'app': id,
            'fields[0]' : 'ID',
            'fields[1]' : 'Name',
            'query' : base_query + (' offset ' + str(offset) if offset > 0 else ''),
            'totalCount': 'false' if offset > 0 else 'true'
        }
        
        url = 'https://' + domain + '/k/v1/records.json?' + getQueryString(params_array)
        res = requests.get(url, headers=headers)
        res_json = res.json()
        records += res_json['records']
        if 'totalCount' in res_json and res_json['totalCount'] is not None:
            totalcount = int(res_json['totalCount'])
        if totalcount == 0:
            break
        offset += limit
        if offset >= totalcount:
            break
    return records

def fetchAttendanceRecords(domain, id, api_token, period_days):
    # kintone から指定した期間分の出席情報を取得
    limit = 500
    headers = {"X-Cybozu-API-Token": api_token}
    base_query = 'attend_at >= FROM_TODAY(' + str(-period_days) + ', DAYS) ' \
         + 'order by attend_at asc ' \
         + 'limit ' + str(limit)
    offset = 0
    totalcount = 0
    records = []
    while True:
        params_array = {
            'app': id,
            'fields[0]' : 'student_id',
            'fields[1]' : 'attend_at',
            'query'     : base_query + (' offset ' + str(offset) if offset > 0 else ''),
            'totalCount': 'false' if offset > 0 else 'true' 
        }
        
        url = 'https://' + domain + '/k/v1/records.json?' + getQueryString(params_array)
        res = requests.get(url, headers=headers)
        res_json = res.json()
        records += res_json['records']
        if 'totalCount' in res_json and res_json['totalCount'] is not None:
            totalcount = int(res_json['totalCount'])
        if totalcount == 0:
            break
        offset += limit
        if offset >= totalcount:
            break
    return records


def normalizeStudentRecords(records):
    students = {}
    for record in records:
        id = int(record['ID']['value'].split('-')[-1])
        name = record['Name']['value']
        students[id] =  {'name': name}
    return students

def normalizeAttendanceRecords(records):
    attends = []
    for record in records:
        id = int(record['student_id']['value'])
        dt = record['attend_at']['value']
        # datetime.datetime.fromisoformat が '2020-01-01T00:00:00Z' の形式に対応していない
        dt = dt.replace('Z', '+00:00')
        attends.append({'student_id':id, 'attend_at':datetime.datetime.fromisoformat(dt)})
    return attends

def getRecentAttendance(attendance_info_list):
    # 生徒毎の最近の出席日を取得
    recent = {}
    for info in attendance_info_list:
        id = info['student_id']
        attend_at = info['attend_at']
        if id in recent:
            if attend_at > recent[id]:
                recent[id] = attend_at
        else:
            recent[id] = attend_at
    return recent


def getThresholdDatetime(absence_days):
    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=absence_days)

def getAbsenceStudents(students, recent_attendance, threshold_datetime):
    # absence_days日間出席していない生徒を返す。出席情報がない場合は、attend_at: 1970/1/1 0:00:00 とする
    asence_students = []
    for student_id in students:
        name = students[student_id]['name']
        if student_id in recent_attendance:
            if recent_attendance[student_id] < threshold_datetime:
                asence_students.append({'name':name, 'attend_at':recent_attendance[student_id]})
        else:
            asence_students.append({'name':name, 'attend_at':DT0})
    asence_students = sorted(asence_students, key=itemgetter('attend_at'), reverse=True)
    return asence_students


def getStudentsInfoMessage(students):
    # ユーザーの情報を取得
    msg = ''
    for student in students:
        attend_at = student['attend_at']
        attend_at_msg = ''
        if attend_at != DT0:
            attend_at_msg += '  ' + datetime.datetime.strftime(attend_at, '%Y/%m/%d')
        msg += student['name'] + attend_at_msg + "\n"
    return msg

def notifySlack(conf, message):
    if 'access_token' not in conf or 'channel' not in conf:
        print('Error: access_token or channel is not found.')
        return False
    client = slack.WebClient(token=conf['access_token'])
    response = client.chat_postMessage(
        channel=conf['channel'],
        text=message)
    if response["ok"] is False:
        if  response["headers"]["Retry-After"]:
            # リトライ時間が設定されているなら再度挑戦
            delay = int(response["headers"]["Retry-After"])
            print('Rate limited. Retrying in ' + str(delay) + ' seconds')
            time.sleep(delay)
            return notifySlack(conf, message)
        print('Error: slack error.')
        return False
    return True

def notifyLine(conf, message):
    if 'access_token' not in conf or 'to' not in conf:
        print('Error: "access_token" or "to" is not found.')
        return False

    # TODO: 
    # アカウント設定 -> チャットへの参加 : 「グループ・複数人チャットへの参加を許可する」にチェック
    # 権限管理 : 必要なユーザーを追加
    # Web hook で、POSTの内容を受け取らないとグループIDが分からない
    # # 月額プラン: フリー の場合、月1000件のメッセージが送信可能
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + conf['access_token']
    }
    body = {
        'to': conf['to'],
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }
    res = requests.post(
        'https://api.line.me/v2/bot/message/push',
        json.dumps(body),
        headers=headers)
    if res.status_code != 200:
        print('StatusCode: ' + str(res.status_code) + "\n")
        print(res.text)
        return False
    return True

if __name__ == '__main__':
    f = open(CONFFILE, 'r')
    conf = json.load(f)
    
    kintone_conf = conf['kintone']
    kintone_domain = kintone_conf['subdomain'] + '.cybozu.com'

    # 何日間欠席が続くと通知するか
    absence_days = DEFAULT_ABSENCE_DAYS
    if 'absence_days' in kintone_conf:
        absence_days = int(kintone_conf['absence_days'])

    students = normalizeStudentRecords(fetchStudentRecords(kintone_domain, kintone_conf['student_app'], kintone_conf['student_token']))
    recent_attendance = getRecentAttendance(normalizeAttendanceRecords(fetchAttendanceRecords(kintone_domain, kintone_conf['attend_app'], kintone_conf['attend_token'], DEFAULT_PERIOD_DAYS)))
    absence_students = getAbsenceStudents(students, recent_attendance, getThresholdDatetime(absence_days))

    msg = str(absence_days) + '日間以上来ていない生徒' + "\n"
    msg += getStudentsInfoMessage(absence_students)
    if 'notify' in conf:
        notify_conf = conf['notify']
        if 'slack' in notify_conf:
            notifySlack(notify_conf['slack'], msg)
        if 'line' in notify_conf:
            notifyLine(notify_conf['line'], msg)
    else:
        print(msg)
