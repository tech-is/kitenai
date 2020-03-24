import unittest
from pathlib import Path
import sys
import datetime
sys.path.append(str(Path(__file__).parent.parent))
from kitenai import normalizeStudentRecords, normalizeAttendanceRecords, getRecentAttendance, getAbsenceStudents

JST = datetime.timezone(datetime.timedelta(hours=+9))
DT0 = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

class NormalizeStudentRecordsTest(unittest.TestCase):
    def test_normalizeStudentRecords_1(self):
        normalized = normalizeStudentRecords([])
        self.assertIsInstance(normalized, dict)
        self.assertEqual(len(normalized), 0)

    def test_normalizeStudentRecords_2(self):
        data = [
            {
                "ID":{
                    "type": "RECORD_NUMBER",
                    "value": "STUDENT-1"
                },
                "Name":{
                    "type": "SINGLE_LINE_TEXT",
                    "value": "生徒1"
                }
            }
        ]
        normalized = normalizeStudentRecords(data)
        self.assertIsInstance(normalized, dict)
        self.assertEqual(len(normalized), 1)
        self.assertTrue(1 in normalized)
        self.assertEqual(normalized[1]['name'], '生徒1')
        
    def test_normalizeStudentRecords_3(self):
        data = [
            {
                "ID":{
                    "type": "RECORD_NUMBER",
                    "value": "STUDENT-1"
                },
                "Name":{
                    "type": "SINGLE_LINE_TEXT",
                    "value": "生徒1"
                }
            },
            {
                "ID":{
                    "type": "RECORD_NUMBER",
                    "value": "STUDENT-2"
                },
                "Name":{
                    "type": "SINGLE_LINE_TEXT",
                    "value": "生徒 2"
                }
            },
            {
                "ID":{
                    "type": "RECORD_NUMBER",
                    "value": "STUDENT-10"
                },
                "Name":{
                    "type": "SINGLE_LINE_TEXT",
                    "value": "生徒 10"
                }
            }
        ]
        normalized = normalizeStudentRecords(data)
        self.assertIsInstance(normalized, dict)
        self.assertEqual(len(normalized), 3)
        self.assertTrue(1 in normalized)
        self.assertTrue(2 in normalized)
        self.assertTrue(10 in normalized)
        self.assertEqual(normalized[1]['name'], '生徒1')
        self.assertEqual(normalized[2]['name'], '生徒 2')
        self.assertEqual(normalized[10]['name'], '生徒 10')

class NormalizeAttendanceRecordsTest(unittest.TestCase):
    def test_normalizeAttendanceRecords_1(self):
        normalized = normalizeAttendanceRecords([])
        self.assertIsInstance(normalized, list)
        self.assertEqual(len(normalized), 0)

    def test_normalizeAttendanceRecords_2(self):
        data = [
            {
                "attend_at":{
                    "type": "DATETIME",
                    "value": "2020-01-27T04:55:00Z"
                },
                "student_id":{
                    "type": "NUMBER",
                    "value": "4"
                }
            }
        ]
        normalized = normalizeAttendanceRecords(data)
        self.assertIsInstance(normalized, list)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]['student_id'], 4)
        self.assertEqual(normalized[0]['attend_at'], datetime.datetime(2020, 1, 27, 4, 55, 0, tzinfo=datetime.timezone.utc))

    def test_normalizeAttendanceRecords_3(self):
        data = [
            {
                "attend_at":{
                    "type": "DATETIME",
                    "value": "2020-01-27T04:55:00Z"
                },
                "student_id":{
                    "type": "NUMBER",
                    "value": "4"
                }
            },
            {
                "attend_at":{
                    "type": "DATETIME",
                    "value": "2020-01-23T04:05:00Z"
                },
                "student_id":{
                    "type": "NUMBER",
                    "value": "1"
                }
            }
        ]
        normalized = normalizeAttendanceRecords(data)
        self.assertIsInstance(normalized, list)
        self.assertEqual(len(normalized), 2)
        self.assertEqual(normalized[0]['student_id'], 4)
        self.assertEqual(normalized[0]['attend_at'], datetime.datetime(2020, 1, 27, 4, 55, 0, tzinfo=datetime.timezone.utc))
        self.assertEqual(normalized[1]['student_id'], 1)
        self.assertEqual(normalized[1]['attend_at'], datetime.datetime(2020, 1, 23, 4, 5, 0, tzinfo=datetime.timezone.utc))

class GetRecentAttendanceTest(unittest.TestCase):
    def test_getRecentAttendance_1(self):
        students = getRecentAttendance([])
        self.assertIsInstance(students, dict)
        self.assertEqual(len(students), 0)

    def test_getRecentAttendance_2(self):
        data = [
            {
                "student_id": 1,
                "attend_at": datetime.datetime(2020, 1, 27, 4, 55, 0, tzinfo=datetime.timezone.utc)
            }
        ]
        students = getRecentAttendance(data)
        self.assertIsInstance(students, dict)
        self.assertEqual(len(students), 1)
        self.assertTrue(1 in students)
        self.assertEqual(students[1], datetime.datetime(2020, 1, 27, 4, 55, 0, tzinfo=datetime.timezone.utc))

    def test_getRecentAttendance_3(self):
        data = [
            {
                "student_id": 1,
                "attend_at": datetime.datetime(2020, 1, 27, 4, 55, 0, tzinfo=datetime.timezone.utc)
            },
            {
                "student_id": 3,
                "attend_at": datetime.datetime(2020, 1, 2, 3, 45, 6, tzinfo=datetime.timezone.utc)
            },
            {
                "student_id": 10,
                "attend_at": datetime.datetime(2020, 1, 23, 4, 55, 0, tzinfo=datetime.timezone.utc)
            },
            {
                "student_id": 3,
                "attend_at": datetime.datetime(2020, 1, 2, 12, 45, 5, tzinfo=JST)
            },
            {
                "student_id": 1,
                "attend_at": datetime.datetime(2020, 2, 20, 20, 20, 20, tzinfo=datetime.timezone.utc)
            }
        ]
        students = getRecentAttendance(data)
        self.assertIsInstance(students, dict)
        self.assertEqual(len(students), 3)
        self.assertTrue(1 in students)
        self.assertEqual(students[1], datetime.datetime(2020, 2, 20, 20, 20, 20, tzinfo=datetime.timezone.utc))
        self.assertTrue(3 in students)
        self.assertEqual(students[3], datetime.datetime(2020, 1, 2, 3, 45, 6, tzinfo=datetime.timezone.utc))
        self.assertTrue(10 in students)
        self.assertEqual(students[10], datetime.datetime(2020, 1, 23, 4, 55, 0, tzinfo=datetime.timezone.utc))


class GetAbsenceStudentsTest(unittest.TestCase):
    def test_getAbsenceStudents_1(self):
        students = {
        }
        recent = {
            1: datetime.datetime(2020, 1, 20, 9, 0, 0, tzinfo=JST)
        }
        absence_students = getAbsenceStudents(students, recent, datetime.datetime(2020, 2, 20, 9, 0, 0, tzinfo=JST))
        self.assertIsInstance(absence_students, list)
        self.assertEqual(len(absence_students), 0)

    def test_getAbsenceStudents_2(self):
        students = {
            1: {'name': 'student1'}
        }
        recent = {
        }
        absence_students = getAbsenceStudents(students, recent, datetime.datetime(2020, 2, 20, 9, 0, 0, tzinfo=JST))
        self.assertIsInstance(absence_students, list)
        self.assertEqual(len(absence_students), 1)
        self.assertEqual(absence_students[0]['name'], 'student1')
        self.assertEqual(absence_students[0]['attend_at'], datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc))

    def test_getAbsenceStudents_3(self):
        students = {
            1: {'name': 'student1'},
            2: {'name': 'student2'},
            3: {'name': 'student3'},
            10: {'name': 'student 10'}
        }
        recent = {
            1: datetime.datetime(2020, 1, 20, 9, 0, 0, tzinfo=JST),
            2: datetime.datetime(2020, 2, 20, 9, 1, 0, tzinfo=JST),
            3: datetime.datetime(2020, 1, 20, 9, 1, 0, tzinfo=JST)
        }
        absence_students = getAbsenceStudents(students, recent, datetime.datetime(2020, 2, 20, 9, 0, 0, tzinfo=JST))
        self.assertIsInstance(absence_students, list)
        self.assertEqual(len(absence_students), 3)
        self.assertEqual(absence_students[0]['name'], 'student3')
        self.assertEqual(absence_students[0]['attend_at'], datetime.datetime(2020, 1, 20, 9, 1, 0, tzinfo=JST))
        self.assertEqual(absence_students[1]['name'], 'student1')
        self.assertEqual(absence_students[1]['attend_at'], datetime.datetime(2020, 1, 20, 9, 0, 0, tzinfo=JST))
        self.assertEqual(absence_students[2]['name'], 'student 10')
        self.assertEqual(absence_students[2]['attend_at'], DT0)
