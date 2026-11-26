import unittest
from datetime import datetime, timedelta, timezone
from io import BytesIO

from openpyxl import load_workbook
from report_export import build_workbook


class ExcelReportTests(unittest.TestCase):
    def test_typed_data_and_incomplete_visits(self):
        def event(id, time):
            return {'id': id, 'created_at': time, 'camera_name': '=1+1'}
        report = {
            'summary': [
                {'plate': '001234', 'entries': 1, 'exits': 1, 'complete': 1,
                 'duration_seconds': 90061, 'open': 0, 'review': 0},
                {'plate': '29E01551', 'entries': 1, 'exits': 0, 'complete': 0,
                 'duration_seconds': 0, 'open': 1, 'review': 0},
            ],
            'visits': [
                {'plate': '001234', 'entry': event(1, '2026-11-10T18:00:00+00:00'),
                 'exit': event(2, '2026-11-11T19:01:01+00:00'), 'status': 'complete', 'duration_seconds': 90061},
                {'plate': '29E01551', 'entry': event(3, '2026-11-11T00:00:00+00:00'),
                 'exit': None, 'status': 'open', 'duration_seconds': None},
            ],
        }
        # Exports all rows, not merely one page of 30.
        report['visits'] += [dict(report['visits'][1]) for _ in range(35)]
        data = build_workbook(report, 'plate=29E01551&status=open&camera=1',
                              [{'id': 1, 'name': 'Cổng vào', 'code': 'IN'}],
                              datetime(2026, 11, 11, tzinfo=timezone.utc))
        book = load_workbook(BytesIO(data))
        self.assertEqual(book.sheetnames, ['Tổng hợp', 'Chi tiết', 'Thông tin'])
        summary, detail = book['Tổng hợp'], book['Chi tiết']
        self.assertEqual(summary['A4'].value, '001234')
        self.assertEqual(summary['A4'].data_type, 's')
        self.assertEqual(summary['A5'].value, '29E01551')
        self.assertEqual(summary['E4'].value, timedelta(seconds=90061))
        self.assertEqual(summary['E4'].number_format, '[h]:mm:ss')
        self.assertIsNone(summary['E5'].value)
        self.assertIsNone(summary['F5'].value)
        self.assertEqual(detail['B4'].value, datetime(2026, 11, 11, 1))
        self.assertEqual(detail['C4'].value, '=1+1')
        self.assertEqual(detail['C4'].data_type, 's')
        self.assertIsNone(detail['D5'].value)
        self.assertIsNone(detail['F5'].value)
        self.assertEqual(detail['G5'].value, 'Chưa ghi nhận ra')
        self.assertEqual(detail.max_row, 40)
        self.assertEqual(detail.freeze_panes, 'B4')
        self.assertGreaterEqual(detail.column_dimensions['B'].width, 25)
        values = list(book['Thông tin'].values)
        self.assertIn(('Camera', 'Cổng vào (IN)'), values)
        self.assertIn(('Trạng thái', 'Chưa ghi nhận ra'), values)

    def test_empty_and_zero_duration(self):
        book = load_workbook(BytesIO(build_workbook({'summary': [], 'visits': []}, '')))
        self.assertEqual(book['Tổng hợp'].max_row, 3)
        report = {'summary': [{'plate': '30A12345', 'entries': 1, 'exits': 1, 'complete': 1,
                               'duration_seconds': 0, 'open': 0, 'review': 0}], 'visits': []}
        book = load_workbook(BytesIO(build_workbook(report, '')))
        self.assertEqual(book['Tổng hợp']['E4'].value, timedelta(0))


if __name__ == '__main__':
    unittest.main()
