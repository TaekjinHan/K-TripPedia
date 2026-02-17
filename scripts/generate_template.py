import pandas as pd
import os

# 파일명 설정
FILE_NAME = "HitoriOk_Data_Template.xlsx"

# 1. places 시트 데이터 (서울 10선 샘플)
places_data = [
    {"name_ko": "명동교자 본점", "name_ja": "ミョンドンギョザ 本店", "category": "noodle", "address": "서울 중구 명동10길 29", "lat": 37.5636, "lng": 126.9854, "phone": "02-776-5348", "opening_hours": "10:30-21:00", "solo_ok_level": "HIGH", "solo_allowed": "YES", "min_portions": 1, "counter_seat": "Y", "best_time_note": "14~17시 여유"},
    {"name_ko": "우래옥", "name_ja": "ウレオッ", "category": "noodle", "address": "서울 중구 창경궁로 62-29", "lat": 37.5682, "lng": 126.9993, "phone": "02-2265-0151", "opening_hours": "11:30-21:00", "solo_ok_level": "MID", "solo_allowed": "YES", "min_portions": 1, "counter_seat": "N", "best_time_note": "오픈런 추천"},
    {"name_ko": "을지면옥", "name_ja": "ウルジミョノッ", "category": "noodle", "address": "서울 중구 을지로19길 6", "lat": 37.5671, "lng": 126.9912, "phone": "02-2266-7052", "opening_hours": "11:00-21:00", "solo_ok_level": "HIGH", "solo_allowed": "YES", "min_portions": 1, "counter_seat": "Y", "best_time_note": "혼밥러 많음"},
    {"name_ko": "이루야 라멘", "name_ja": "イルヤラーメン", "category": "noodle", "address": "서울 중구 충무로9길 17", "lat": 37.5651, "lng": 126.9934, "phone": "02-123-4567", "opening_hours": "11:00-21:00", "solo_ok_level": "HIGH", "solo_allowed": "YES", "min_portions": 1, "counter_seat": "Y", "best_time_note": "카운터석 위주"},
    {"name_ko": "진옥화할매원조닭한마리", "name_ja": "ジンオックァ", "category": "chicken", "address": "서울 종로구 종로40가길 18", "lat": 37.5702, "lng": 127.0062, "phone": "02-2275-9666", "opening_hours": "10:30-01:00", "solo_ok_level": "LOW", "solo_allowed": "CONDITIONAL", "min_portions": 2, "counter_seat": "N", "best_time_note": "2인분 주문 필수"},
    {"name_ko": "채선당 명동점", "name_ja": "チェソンダン", "category": "shabu", "address": "서울 중구 명동길 12", "lat": 37.5645, "lng": 126.9821, "phone": "02-310-9288", "opening_hours": "11:00-21:00", "solo_ok_level": "MID", "solo_allowed": "YES", "min_portions": 1, "counter_seat": "N", "best_time_note": "평일 낮 추천"},
    {"name_ko": "통인시장 도시락카페", "name_ja": "通仁市場", "category": "korean", "address": "서울 종로구 자하문로15길 18", "lat": 37.5806, "lng": 126.9696, "phone": "02-722-0911", "opening_hours": "11:00-16:00", "solo_ok_level": "HIGH", "solo_allowed": "YES", "min_portions": 1, "counter_seat": "Y", "best_time_note": "엽전 도시락 재미"},
    {"name_ko": "호랑이떡볶이", "name_ja": "ホランイ", "category": "snack", "address": "서울 종로구 종로3길 17", "lat": 37.5711, "lng": 126.9798, "phone": "010-1234-5678", "opening_hours": "12:00-20:00", "solo_ok_level": "HIGH", "solo_allowed": "YES", "min_portions": 1, "counter_seat": "Y", "best_time_note": "혼떡 가능"},
    {"name_ko": "네네치킨 종로점", "name_ja": "ネネチキン", "category": "chicken", "address": "서울 종로구 종로 53", "lat": 37.5705, "lng": 126.9832, "phone": "02-733-4479", "opening_hours": "15:00-02:00", "solo_ok_level": "MID", "solo_allowed": "YES", "min_portions": 1, "counter_seat": "N", "best_time_note": "배달 위주나 홀 가능"},
    {"name_ko": "부산집", "name_ja": "プサンジッ", "category": "izakaya", "address": "서울 중구 다산로 149", "lat": 37.5582, "lng": 127.0123, "phone": "02-2234-1234", "opening_hours": "17:00-03:00", "solo_ok_level": "MID", "solo_allowed": "YES", "min_portions": 1, "counter_seat": "Y", "best_time_note": "카운터 오뎅바"}
]

# 2. rules 시트 데이터 (샘플)
rules_data = [
    {"place_name_ko": "진옥화할매원조닭한마리", "rule_type": "MIN_ORDER", "note_short": "솔로 방문 시에도 한 마리 주문 필수", "value_int": 2, "value_text": "", "dow": "", "start_time": "", "end_time": "", "window_kind": ""},
    {"place_name_ko": "명동교자 본점", "rule_type": "MIN_ORDER", "note_short": "1인 1국시 필수", "value_int": 1, "value_text": "", "dow": "", "start_time": "", "end_time": "", "window_kind": ""}
]

# 3. tips 시트 데이터 (샘플)
tips_data = [
    {"place_name_ko": "명동교자 본점", "tip_type": "ORDER", "tip_text_ko": "칼국수는 리필이 됩니다(무료).", "tip_text_ja": "カルグクスはお代わり自由です。", "tip_text_en": "Free refills for Kalguksu.", "priority": 100},
    {"place_name_ko": "통인시장 도시락카페", "tip_type": "ETC", "tip_text_ko": "엽전을 사서 돌아다니며 담는 재미가 있습니다.", "tip_text_ja": "古い小銭をかって市場を回る楽しみがあります。", "tip_text_en": "Buy coins to pick food across market.", "priority": 100}
]

def create_excel():
    print(f"[START] Creating {FILE_NAME}...")
    
    # 데이터프레임 생성
    df_places = pd.DataFrame(places_data)
    df_rules = pd.DataFrame(rules_data)
    df_tips = pd.DataFrame(tips_data)
    
    # 엑셀 파일로 저장
    with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
        df_places.to_excel(writer, sheet_name='places', index=False)
        df_rules.to_excel(writer, sheet_name='rules', index=False)
        df_tips.to_excel(writer, sheet_name='tips', index=False)
        
    # 스타일링 (컬럼 너비 조정 등)
    
    print(f"[DONE] File created: {os.path.abspath(FILE_NAME)}")

if __name__ == "__main__":
    try:
        import openpyxl
    except ImportError:
        os.system("pip install openpyxl")
        
    create_excel()
