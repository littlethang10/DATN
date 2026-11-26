"""Create typed Excel reports without letting Excel reinterpret plate strings."""
from datetime import datetime, timedelta, timezone
from io import BytesIO
from urllib.parse import parse_qs

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

LOCAL_TZ = timezone(timedelta(hours=7))
DATE_FORMAT = 'dd/mm/yyyy hh:mm:ss'
DURATION_FORMAT = '[h]:mm:ss'
STATUSES = {'complete': 'Đã ra', 'open': 'Chưa ghi nhận ra',
            'missing_in': 'Thiếu lượt vào', 'review': 'Cần kiểm tra'}
FILTER_NAMES = {
    'start': 'Từ ngày', 'end': 'Đến ngày', 'plate': 'Biển số',
    'status': 'Trạng thái', 'camera': 'Camera', 'plate_mode': 'Kiểu tìm biển số',
    'time_field': 'Thời điểm lọc', 'time_start': 'Giờ từ', 'time_end': 'Giờ đến',
    'entry_camera': 'Camera vào', 'exit_camera': 'Camera ra',
    'duration_min': 'Lưu trú từ (phút)', 'duration_max': 'Lưu trú đến (phút)',
    'confidence_side': 'Áp dụng độ tin cậy', 'image': 'Ảnh toàn khung hình',
    'event_id': 'Mã sự kiện',
}
for prefix, label in [('detection_confidence', 'Độ tin cậy phát hiện'),
                      ('ocr_confidence', 'Độ tin cậy OCR'),
                      ('entry_count', 'Số lượt vào'), ('exit_count', 'Số lượt ra')]:
    for suffix, word in [('min', 'từ'), ('max', 'đến')]:
        FILTER_NAMES[f'{prefix}_{suffix}'] = f'{label} {word}' + (' (%)' if 'confidence' in prefix else '')
FILTER_VALUES = {
    'status': {'all': 'Tất cả', **STATUSES},
    'plate_mode': {'partial': 'Chứa nội dung', 'exact': 'Chính xác'},
    'time_field': {'anchor': 'Ngày vào; thiếu vào dùng ngày ra', 'entry': 'Thời gian vào',
                   'exit': 'Thời gian ra', 'either': 'Vào hoặc ra'},
    'confidence_side': {'either': 'Một sự kiện vào hoặc ra', 'entry': 'Sự kiện vào', 'exit': 'Sự kiện ra'},
    'image': {'all': 'Tất cả', 'yes': 'Có ảnh ở ít nhất một sự kiện', 'no': 'Thiếu ảnh ở ít nhất một sự kiện'},
}


def local_datetime(value):
    if not value:
        return None
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(LOCAL_TZ).replace(tzinfo=None)


def duration_value(seconds):
    return None if seconds is None else timedelta(seconds=seconds)


def append_values(sheet, values):
    sheet.append(values)
    for cell in sheet[sheet.max_row]:
        # Literal strings preserve leading zeros and never become formulas.
        if isinstance(cell.value, str):
            cell.data_type = 's'
            cell.number_format = '@'


def table_sheet(book, name, title, headers, widths, rows, date_cols=(), duration_cols=()):
    sheet = book.create_sheet(name)
    last = get_column_letter(len(headers))
    sheet.merge_cells(f'A1:{last}1')
    sheet['A1'] = title
    sheet['A1'].font = Font(name='Calibri', size=16, bold=True, color='17365D')
    sheet.row_dimensions[1].height = 30
    sheet.merge_cells(f'A2:{last}2')
    sheet['A2'] = 'Múi giờ UTC+7. Thời gian lưu trú: tổng giờ:phút:giây; ô trống nghĩa là chưa xác định.'
    sheet['A2'].alignment = Alignment(wrap_text=True, vertical='center')
    sheet.row_dimensions[2].height = 32
    sheet.append(headers)
    for row in rows:
        append_values(sheet, row)
    for cell in sheet[3]:
        cell.font = Font(name='Calibri', bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='17365D')
        cell.alignment = Alignment(wrap_text=True, vertical='center')
    sheet.row_dimensions[3].height = 34
    for row in sheet.iter_rows(min_row=4):
        for cell in row:
            cell.font = Font(name='Calibri', size=11)
            cell.alignment = Alignment(vertical='center', wrap_text=True)
            if cell.row % 2 == 0:
                cell.fill = PatternFill('solid', fgColor='F0F5FB')
            if cell.column in date_cols:
                cell.number_format = DATE_FORMAT
            elif cell.column in duration_cols:
                cell.number_format = DURATION_FORMAT
        sheet.row_dimensions[row[0].row].height = 32
    for column, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(column)].width = width
    sheet.auto_filter.ref = f'A3:{last}{max(3, sheet.max_row)}'
    sheet.freeze_panes = 'B4'
    sheet.sheet_view.showGridLines = False
    sheet.print_title_rows = '1:3'
    sheet.print_options.horizontalCentered = True
    sheet.page_setup.orientation = 'landscape'
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_margins = PageMargins(left=.25, right=.25, top=.4, bottom=.4, header=.15, footer=.2)
    sheet.print_area = f'A1:{last}{max(3, sheet.max_row)}'
    sheet.oddFooter.center.text = 'Trang &P / &N'
    return sheet


def build_workbook(report, query, cameras=(), exported_at=None):
    book = Workbook()
    book.remove(book.active)
    summary_rows = []
    for item in report['summary']:
        total = item['duration_seconds'] if item['complete'] else None
        average = total / item['complete'] if total is not None else None
        summary_rows.append([str(item['plate']), item['entries'], item['exits'], item['complete'],
                             duration_value(total), duration_value(average), item['open'], item['review']])
    table_sheet(book, 'Tổng hợp', 'TỔNG HỢP THEO BIỂN SỐ',
                ['Biển số', 'Lượt vào', 'Lượt ra', 'Lượt hoàn chỉnh', 'Tổng thời gian lưu trú',
                 'Thời gian trung bình', 'Chưa ghi nhận ra', 'Cần kiểm tra / thiếu vào'],
                [20, 12, 12, 16, 24, 24, 20, 26], summary_rows, duration_cols=(5, 6))
    detail_rows = []
    for visit in report['visits']:
        entry, exit_event = visit['entry'] or {}, visit['exit'] or {}
        detail_rows.append([str(visit['plate']), local_datetime(entry.get('created_at')),
                            entry.get('camera_name'), local_datetime(exit_event.get('created_at')),
                            exit_event.get('camera_name'),
                            duration_value(visit['duration_seconds']) if visit['status'] == 'complete' else None,
                            STATUSES.get(visit['status'], visit['status']), entry.get('id'), exit_event.get('id')])
    detail = table_sheet(book, 'Chi tiết', 'CHI TIẾT LƯỢT PHƯƠNG TIỆN',
                         ['Biển số', 'Thời gian vào', 'Camera vào', 'Thời gian ra', 'Camera ra',
                          'Thời gian lưu trú', 'Trạng thái', 'Mã sự kiện vào', 'Mã sự kiện ra'],
                         [20, 25, 22, 25, 22, 22, 25, 16, 16], detail_rows,
                         date_cols=(2, 4), duration_cols=(6,))
    for row in detail.iter_rows(min_row=4):
        status = row[6]
        if status.value:
            status.fill = PatternFill('solid', fgColor='E2F0D9' if status.value == STATUSES['complete'] else 'FFF2CC')
    created = (exported_at or datetime.now(timezone.utc)).astimezone(LOCAL_TZ)
    info_rows = [
        ['Thời điểm xuất (UTC+7)', created.strftime('%d/%m/%Y %H:%M:%S')],
        ['Số biển số trong báo cáo', len(report['summary'])],
        ['Số dòng chi tiết', len(report['visits'])],
        ['Lượt hoàn chỉnh', sum(v['status'] == 'complete' for v in report['visits'])],
        ['Cách tính thời gian', 'Chỉ tính cho lượt hoàn chỉnh. Lượt thiếu thông tin hoặc cần kiểm tra để trống thời gian.'],
        ['Cách đọc thời lượng', 'Định dạng [h]:mm:ss giữ tổng số giờ kể cả khi trên 24 giờ.'],
        ['Đối chiếu dữ liệu', 'Biển số giữ nguyên kết quả đã lưu. Kiểm tra ảnh sự kiện khi OCR sai hoặc thiếu lượt; báo cáo không tự sửa biển số.'],
        ['Phạm vi', 'Áp dụng cùng bộ lọc với trang lịch sử, bao gồm toàn bộ các trang kết quả. Ghép sự kiện trước khi lọc.'],
    ]
    camera_names = {str(c['id']): f"{c['name']} ({c['code']})" for c in cameras}
    for key, values in parse_qs(query).items():
        value = values[0]
        if key in ('camera', 'entry_camera', 'exit_camera'):
            value = 'Tất cả camera' if value == 'all' else camera_names.get(value, value)
        else:
            value = FILTER_VALUES.get(key, {}).get(value, value)
        info_rows.append([FILTER_NAMES.get(key, key), value])
    info = table_sheet(book, 'Thông tin', 'THÔNG TIN BÁO CÁO GATEVIEW',
                       ['Nội dung', 'Giá trị'], [34, 100], info_rows)
    for row in range(4, info.max_row + 1):
        info.row_dimensions[row].height = 44
    output = BytesIO()
    book.save(output)
    return output.getvalue()
