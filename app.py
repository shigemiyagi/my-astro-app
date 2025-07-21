import streamlit as st
import swisseph as swe
from datetime import datetime, timezone, timedelta
import os
import math

# --- 都道府県の緯度経度データ ---
prefecture_data = {
    "北海道": {"lat": 43.064, "lon": 141.348}, "青森県": {"lat": 40.825, "lon": 140.741},
    "岩手県": {"lat": 39.704, "lon": 141.153}, "宮城県": {"lat": 38.269, "lon": 140.872},
    "秋田県": {"lat": 39.719, "lon": 140.102}, "山形県": {"lat": 38.240, "lon": 140.364},
    "福島県": {"lat": 37.750, "lon": 140.468}, "茨城県": {"lat": 36.342, "lon": 140.447},
    "栃木県": {"lat": 36.566, "lon": 139.884}, "群馬県": {"lat": 36.391, "lon": 139.060},
    "埼玉県": {"lat": 35.857, "lon": 139.649}, "千葉県": {"lat": 35.605, "lon": 140.123},
    "東京都": {"lat": 35.690, "lon": 139.692}, "神奈川県": {"lat": 35.448, "lon": 139.643},
    "新潟県": {"lat": 37.902, "lon": 139.023}, "富山県": {"lat": 36.695, "lon": 137.211},
    "石川県": {"lat": 36.594, "lon": 136.626}, "福井県": {"lat": 36.065, "lon": 136.222},
    "山梨県": {"lat": 35.664, "lon": 138.568}, "長野県": {"lat": 36.651, "lon": 138.181},
    "岐阜県": {"lat": 35.391, "lon": 136.722}, "静岡県": {"lat": 34.977, "lon": 138.383},
    "愛知県": {"lat": 35.180, "lon": 136.907}, "三重県": {"lat": 34.730, "lon": 136.509},
    "滋賀県": {"lat": 35.005, "lon": 135.869}, "京都府": {"lat": 35.021, "lon": 135.756},
    "大阪府": {"lat": 34.686, "lon": 135.520}, "兵庫県": {"lat": 34.691, "lon": 135.183},
    "奈良県": {"lat": 34.685, "lon": 135.833}, "和歌山県": {"lat": 34.226, "lon": 135.168},
    "鳥取県": {"lat": 35.504, "lon": 134.238}, "島根県": {"lat": 35.472, "lon": 133.051},
    "岡山県": {"lat": 34.662, "lon": 133.934}, "広島県": {"lat": 34.396, "lon": 132.459},
    "山口県": {"lat": 34.186, "lon": 131.471}, "徳島県": {"lat": 34.066, "lon": 134.559},
    "香川県": {"lat": 34.340, "lon": 134.043}, "愛媛県": {"lat": 33.842, "lon": 132.765},
    "高知県": {"lat": 33.560, "lon": 133.531}, "福岡県": {"lat": 33.607, "lon": 130.418},
    "佐賀県": {"lat": 33.249, "lon": 130.299}, "長崎県": {"lat": 32.745, "lon": 129.874},
    "熊本県": {"lat": 32.790, "lon": 130.742}, "大分県": {"lat": 33.238, "lon": 131.613},
    "宮崎県": {"lat": 31.911, "lon": 131.424}, "鹿児島県": {"lat": 31.560, "lon": 130.558},
    "沖縄県": {"lat": 26.212, "lon": 127.681}
}

# --- 定数リスト ---
SIGN_NAMES = ["牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座", "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"]
GEO_CELESTIAL_NAMES = ["太陽", "月", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星", "キロン", "ドラゴンヘッド", "リリス"]
GEO_CELESTIAL_IDS = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO, swe.CHIRON, swe.MEAN_NODE, swe.MEAN_APOG]
HELIO_CELESTIAL_NAMES = ["地球", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星", "キロン"]
HELIO_CELESTIAL_IDS = [swe.EARTH, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO, swe.CHIRON]
ASPECT_NAMES = {0: "コンジャンクション (0度)", 60: "セクスタイル (60度)", 72: "クインタイル (72度)", 90: "スクエア (90度)", 120: "トライン (120度)", 180: "オポジション (180度)"}
MAJOR_ASPECT_ORB_LUMINARIES, MAJOR_ASPECT_ORB_OTHERS, SEXTILE_ORB, QUINTILE_ORB = 8, 6, 3, 2

# --- 関数定義 ---
def get_house_number(degree, cusps):
    cusps_with_13th = list(cusps) + [cusps[0]]
    for i in range(12):
        start_cusp, end_cusp = cusps_with_13th[i], cusps_with_13th[i+1]
        if start_cusp > end_cusp:
            if degree >= start_cusp or degree < end_cusp: return i + 1
        else:
            if start_cusp <= degree < end_cusp: return i + 1
    return -1

def calculate_aspects(points1, points2, title1, title2, results_list):
    results_list.append(f"\n💫 ## {title1} - {title2} アスペクト ##")
    found = False
    p1_names, p2_names = list(points1.keys()), list(points2.keys())
    for i in range(len(p1_names)):
        for j in range(len(p2_names)):
            if points1 is points2 and i >= j: continue
            p1_name, p2_name = p1_names[i], p2_names[j]
            if p1_name in ["ドラゴンヘッド", "リリス", "キロン"] and p2_name in ["ASC", "MC", "PoF"]: continue
            if p2_name in ["ドラゴンヘッド", "リリス", "キロン"] and p1_name in ["ASC", "MC", "PoF"]: continue
            p1, p2 = points1[p1_name], points2[p2_name]
            is_major_point_involved = p1['is_luminary'] or p2['is_luminary']
            angle = abs(p1['pos'] - p2['pos'])
            if angle > 180: angle = 360 - angle
            for aspect_angle, aspect_name in ASPECT_NAMES.items():
                orb = 0
                if aspect_angle in [0, 90, 120, 180]:
                    orb = MAJOR_ASPECT_ORB_LUMINARIES if is_major_point_involved else MAJOR_ASPECT_ORB_OTHERS
                elif aspect_angle == 60: orb = SEXTILE_ORB
                elif aspect_angle == 72: orb = QUINTILE_ORB
                current_orb = abs(angle - aspect_angle)
                if 0 < orb and current_orb < orb:
                    line = f"{title1}{p1_name} - {title2}{p2_name}: {aspect_name} (オーブ {current_orb:.2f}度)"
                    results_list.append(line)
                    found = True
    if not found: results_list.append("設定されたオーブ内に主要なアスペクトは見つかりませんでした。")

def find_solar_return_jd(birth_time_utc, natal_sun_lon, return_year):
    guess_dt = birth_time_utc.replace(year=return_year)
    jd_current = swe.utc_to_jd(guess_dt.year, guess_dt.month, guess_dt.day, guess_dt.hour, guess_dt.minute, guess_dt.second, 1)[1]
    for _ in range(5):
        res = swe.calc_ut(jd_current, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)
        current_sun_lon, sun_speed = res[0][0], res[0][3]
        if sun_speed == 0: return None
        offset = current_sun_lon - natal_sun_lon
        if offset > 180: offset -= 360
        if offset < -180: offset += 360
        time_adjustment = -offset / sun_speed
        jd_current += time_adjustment
    return jd_current

# --- Streamlit UI設定 ---
st.set_page_config(page_title="西洋占星術カリキュレータ", page_icon="🪐")
st.title("🪐 西洋占星術カリキュレータ")
st.write("出生情報と現在の滞在場所を入力して、ホロスコープを計算します。")

# --- 入力フォーム ---
with st.form(key='birth_info_form'):
    st.subheader("出生情報")
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input("📅 生年月日", min_value=datetime(1900, 1, 1), value=datetime(1976, 12, 25))
    with col2:
        time_str = st.text_input("⏰ 出生時刻", value="16:25")
    selected_prefecture = st.selectbox("📍 出生都道府県", options=list(prefecture_data.keys()), index=46)
    st.markdown("---")
    st.subheader("ソーラーリターン用の情報")
    sr_prefecture = st.selectbox("📍 現在の滞在場所（都道府県）", options=list(prefecture_data.keys()), index=46)
    submit_button = st.form_submit_button(label='ホロスコープを計算する ✨')

# --- ボタンが押されたら計算を実行 ---
if submit_button:
    try:
        birth_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        st.error("時刻の形式が正しくありません。「HH:MM」（例: 16:25）の形式で入力してください。")
        st.stop()

    year, month, day = birth_date.year, birth_date.month, birth_date.day
    hour, minute = birth_time.hour, birth_time.minute
    coords = prefecture_data[selected_prefecture]
    lat, lon = coords["lat"], coords["lon"]
    user_birth_time = datetime(year, month, day, hour, minute)
    birth_time_utc = user_birth_time.replace(tzinfo=timezone(timedelta(hours=9))).astimezone(timezone.utc)
    jd_et = swe.utc_to_jd(birth_time_utc.year, birth_time_utc.month, birth_time_utc.day, birth_time_utc.hour, birth_time_utc.minute, birth_time_utc.second, 1)[1]
    
    today = datetime.now().date()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return_year = today.year

    ephe_path = 'ephe'
    if not os.path.exists(ephe_path):
        st.error(f"天体暦ファイルが見つかりません。'{ephe_path}' フォルダを配置してください。")
        st.stop()
    swe.set_ephe_path(ephe_path)

    iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
    results_to_copy = []
    
    # ... (ジオ、ヘリオ、トランジット、プログレス、ソーラーアーク、ソーラーリターンの計算部分は変更なし) ...
    # 1. ネイタルチャート計算 (ジオセントリック)
    natal_points = {}
    cusps, ascmc = swe.houses(jd_et, lat, lon, b'P')
    for i, p_id in enumerate(GEO_CELESTIAL_IDS):
        res = swe.calc(jd_et, p_id, iflag) if p_id == swe.MEAN_APOG else swe.calc_ut(jd_et, p_id, iflag)
        pos = res[0][0]
        speed = res[0][3] if len(res[0]) > 3 else 0.0
        natal_points[GEO_CELESTIAL_NAMES[i]] = {'id': p_id, 'pos': pos, 'is_retro': speed < 0, 'speed': speed, 'is_luminary': p_id in [swe.SUN, swe.MOON]}
    natal_points["ASC"] = {'id': 'ASC', 'pos': ascmc[0], 'is_retro': False, 'speed': 0, 'is_luminary': True}
    natal_points["MC"] = {'id': 'MC', 'pos': ascmc[1], 'is_retro': False, 'speed': 0, 'is_luminary': True}
    natal_points["PoF"] = {'id': 'PoF', 'pos': (ascmc[0] + natal_points["月"]['pos'] - natal_points["太陽"]['pos']) % 360, 'is_retro': False, 'speed': 0, 'is_luminary': False}

    header_str = f"✨ {birth_date.year}年{birth_date.month}月{birth_date.day}日 {birth_time.strftime('%H:%M')}生 ({selected_prefecture}) - 年齢: {age}歳"
    st.header(header_str)
    results_to_copy.append("--- ジオセントリック ---")
    results_to_copy.append(header_str)
    results_to_copy.append("-" * 40)
    results_to_copy.append("\n🪐 ## ネイタルチャート (ジオセントリック) ##")
    for name, data in natal_points.items():
        pos, sign_index, degree = data['pos'], int(data['pos'] / 30), data['pos'] % 30
        retro_info = "(R)" if data['is_retro'] else ""
        house_num = get_house_number(pos, cusps)
        results_to_copy.append(f"{name:<12}: {SIGN_NAMES[sign_index]:<4} {degree:>5.2f}度 {retro_info:<3} (第{house_num}ハウス)")
    results_to_copy.append("\n🏠 ## ハウス (ネイタル) ##")
    for i in range(12): results_to_copy.append(f"第{i+1:<2}ハウス: {SIGN_NAMES[int(cusps[i] / 30)]:<4} {cusps[i] % 30:.2f}度")
    calculate_aspects(natal_points, natal_points, "N.", "N.", results_to_copy)
    
    # 2. ヘリオセントリック情報
    results_to_copy.append("\n" + "="*40)
    results_to_copy.append("--- ヘリオセントリック ---")
    helio_iflag = iflag | swe.FLG_HELCTR
    helio_points = {}
    for i, p_id in enumerate(HELIO_CELESTIAL_IDS):
        res = swe.calc_ut(jd_et, p_id, helio_iflag)
        pos = res[0][0]
        is_luminary = p_id == swe.EARTH
        helio_points[HELIO_CELESTIAL_NAMES[i]] = {'id': p_id, 'pos': pos, 'is_luminary': is_luminary}
    results_to_copy.append("\n🪐 ## ネイタルチャート (ヘリオセントリック) ##")
    for name, data in helio_points.items():
        pos, sign_index, degree = data['pos'], int(data['pos'] / 30), data['pos'] % 30
        results_to_copy.append(f"{name:<12}: {SIGN_NAMES[sign_index]:<4} {degree:>5.2f}度")
    calculate_aspects(helio_points, helio_points, "H.", "H.", results_to_copy)

    # 3. トランジット情報
    transit_dt_utc = datetime.now(timezone.utc)
    jd_transit = swe.utc_to_jd(transit_dt_utc.year, transit_dt_utc.month, transit_dt_utc.day, transit_dt_utc.hour, transit_dt_utc.minute, transit_dt_utc.second, 1)[1]
    transit_points = {}
    for i, p_id in enumerate(GEO_CELESTIAL_IDS):
        if p_id in [swe.MOON, swe.MEAN_NODE, swe.MEAN_APOG, swe.CHIRON]: continue
        res = swe.calc_ut(jd_transit, p_id, iflag)
        pos, speed = res[0][0], (res[0][3] if len(res[0]) > 3 else 0.0)
        transit_points[GEO_CELESTIAL_NAMES[i]] = {'id': p_id, 'pos': pos, 'is_retro': speed < 0, 'speed': speed, 'is_luminary': p_id in [swe.SUN, swe.MOON]}
    calculate_aspects(transit_points, natal_points, "T.", "N.", results_to_copy)

    # 4. プログレス＆ソーラーアークのための日付計算
    prog_dt_utc = birth_time_utc + timedelta(days=age)
    jd_prog = swe.utc_to_jd(prog_dt_utc.year, prog_dt_utc.month, prog_dt_utc.day, prog_dt_utc.hour, prog_dt_utc.minute, prog_dt_utc.second, 1)[1]
    progressed_points = {}
    for i, p_id in enumerate(GEO_CELESTIAL_IDS):
        if p_id in [swe.MOON, swe.URANUS, swe.NEPTUNE, swe.PLUTO, swe.MEAN_NODE, swe.MEAN_APOG, swe.CHIRON]: continue
        res = swe.calc_ut(jd_prog, p_id, iflag)
        pos, speed = res[0][0], (res[0][3] if len(res[0]) > 3 else 0.0)
        progressed_points[GEO_CELESTIAL_NAMES[i]] = {'id': p_id, 'pos': pos, 'is_retro': speed < 0, 'speed': speed, 'is_luminary': p_id in [swe.SUN, swe.MOON]}
    calculate_aspects(progressed_points, natal_points, "P.", "N.", results_to_copy)
    
    # 5. ソーラーアーク情報
    natal_sun_pos = natal_points["太陽"]['pos']
    progressed_sun_pos = swe.calc_ut(jd_prog, swe.SUN, iflag)[0][0]
    solar_arc = (progressed_sun_pos - natal_sun_pos + 360) % 360
    solar_arc_points = {}
    for name, data in natal_points.items():
        if name in ["PoF", "月"]: continue
        sa_pos = (data['pos'] + solar_arc) % 360
        solar_arc_points[name] = {'id': data['id'], 'pos': sa_pos, 'is_luminary': data['is_luminary']}
    calculate_aspects(solar_arc_points, natal_points, "SA.", "N.", results_to_copy)

    # 6. ソーラーリターン情報
    jd_solar_return = find_solar_return_jd(birth_time_utc, natal_sun_pos, return_year)
    if jd_solar_return is None: st.error("ソーラーリターンの計算に失敗しました。")
    else:
        results_to_copy.append("\n" + "="*40)
        sr_coords = prefecture_data[sr_prefecture]
        sr_lat, sr_lon = sr_coords["lat"], sr_coords["lon"]
        y, m, d, h_decimal = swe.revjul(jd_solar_return, swe.GREG_CAL)
        h, mi, s = int(h_decimal), int((h_decimal - h) * 60), int((((h_decimal - h) * 60) - int((h_decimal - h) * 60)) * 60)
        sr_dt_utc = datetime(y, m, d, h, mi, s, tzinfo=timezone.utc)
        sr_dt_local = sr_dt_utc.astimezone(timezone(timedelta(hours=9)))
        sr_header = f"🎂 ## {return_year}年 ソーラーリターンチャート ##\n({sr_dt_local.strftime('%Y-%m-%d %H:%M:%S')} @ {sr_prefecture})"
        results_to_copy.append("\n" + sr_header)
        solar_return_points = {}
        sr_cusps, sr_ascmc = swe.houses(jd_solar_return, sr_lat, sr_lon, b'P')
        for i, p_id in enumerate(GEO_CELESTIAL_IDS):
            res = swe.calc_ut(jd_solar_return, p_id, iflag)
            pos, speed = res[0][0], (res[0][3] if len(res[0]) > 3 else 0.0)
            solar_return_points[GEO_CELESTIAL_NAMES[i]] = {'id': p_id, 'pos': pos, 'is_retro': speed < 0, 'speed': speed, 'is_luminary': p_id in [swe.SUN, swe.MOON]}
        solar_return_points["ASC"], solar_return_points["MC"] = {'id': 'ASC', 'pos': sr_ascmc[0], 'is_retro': False, 'speed': 0, 'is_luminary': True}, {'id': 'MC', 'pos': sr_ascmc[1], 'is_retro': False, 'speed': 0, 'is_luminary': True}
        results_to_copy.append("\n🪐 ## 惑星のサイン (ソーラーリターン) ##")
        for name, data in solar_return_points.items():
            pos, sign_index, degree = data['pos'], int(data['pos'] / 30), data['pos'] % 30
            retro_info = "(R)" if data['is_retro'] else ""
            house_num = get_house_number(pos, sr_cusps)
            results_to_copy.append(f"{name:<12}: {SIGN_NAMES[sign_index]:<4} {degree:>5.2f}度 {retro_info:<3} (第{house_num}ハウス)")
        results_to_copy.append("\n🏠 ## ハウス (ソーラーリターン) ##")
        for i in range(12): results_to_copy.append(f"第{i+1:<2}ハウス: {SIGN_NAMES[int(sr_cusps[i] / 30)]:<4} {sr_cusps[i] % 30:.2f}度")
        calculate_aspects(solar_return_points, solar_return_points, "SR.", "SR.", results_to_copy)
    
    # ▼▼▼ 7. ハーモニクス情報 ▼▼▼
    results_to_copy.append("\n" + "="*40)
    results_to_copy.append("--- ハーモニクス ---")
    harmonic_numbers = [5, 7, 16, 18, 24, 50]

    for n in harmonic_numbers:
        results_to_copy.append(f"\n🎵 ## H{n} ハーモニクスチャート ##")
        h_points = {}
        # ネイタルのジオセントリック天体（ASC/MC等も含む）をベースに計算
        for name, data in natal_points.items():
            h_pos = (data['pos'] * n) % 360
            h_points[name] = {'id': data['id'], 'pos': h_pos, 'is_luminary': data['is_luminary']}
        
        # ハーモニクスチャートの天体位置を表示
        for name, data in h_points.items():
            pos, sign_index, degree = data['pos'], int(data['pos'] / 30), data['pos'] % 30
            # ハウスや逆行はないのでシンプルに表示
            results_to_copy.append(f"{name:<12}: {SIGN_NAMES[sign_index]:<4} {degree:>5.2f}度")
        
        # ハーモニクスチャート内のアスペクトを計算
        calculate_aspects(h_points, h_points, f"H{n}.", f"H{n}.", results_to_copy)

    # --- コピー用のテキストエリアに全結果を表示 ---
    final_results_string = "\n".join(results_to_copy)
    st.code(final_results_string, language=None)
