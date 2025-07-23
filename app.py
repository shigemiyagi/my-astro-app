import streamlit as st
import swisseph as swe
from datetime import datetime, timezone, timedelta
import os
import math

# --- 定数定義 ---

# 占星術関連
SIGN_NAMES = ["牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座", "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"]
DEGREES_PER_SIGN = 30
ZODIAC_DEGREES = 360

# 天体IDと名前 (ジオセントリック)
GEO_CELESTIAL_BODIES = {
    "太陽": swe.SUN, "月": swe.MOON, "水星": swe.MERCURY, "金星": swe.VENUS,
    "火星": swe.MARS, "木星": swe.JUPITER, "土星": swe.SATURN, "天王星": swe.URANUS,
    "海王星": swe.NEPTUNE, "冥王星": swe.PLUTO, "キロン": swe.CHIRON,
    "ドラゴンヘッド": swe.MEAN_NODE, "リリス": swe.MEAN_APOG
}
# 天体IDと名前 (ヘリオセントリック)
HELIO_CELESTIAL_BODIES = {
    "地球": swe.EARTH, "水星": swe.MERCURY, "金星": swe.VENUS, "火星": swe.MARS,
    "木星": swe.JUPITER, "土星": swe.SATURN, "天王星": swe.URANUS, "海王星": swe.NEPTUNE,
    "冥王星": swe.PLUTO, "キロン": swe.CHIRON
}
# 光度 (Luminaries)
LUMINARIES = [swe.SUN, swe.MOON]
# 感受点
SENSITIVE_POINTS = ["ASC", "MC", "PoF"]

# アスペクト定義
ASPECTS = {
    "コンジャンクション (0度)": {"angle": 0, "orb_lum": 8, "orb_other": 6},
    "オポジション (180度)": {"angle": 180, "orb_lum": 8, "orb_other": 6},
    "トライン (120度)": {"angle": 120, "orb_lum": 8, "orb_other": 6},
    "スクエア (90度)": {"angle": 90, "orb_lum": 8, "orb_other": 6},
    "セクスタイル (60度)": {"angle": 60, "orb_lum": 3, "orb_other": 3},
    "クインタイル (72度)": {"angle": 72, "orb_lum": 2, "orb_other": 2},
}

# ハーモニクス
TARGET_HARMONICS = [5, 7, 16, 18, 24, 50]
HARMONIC_ORB = 2.0

# --- 都道府県データ ---
# (変更なしのため省略)
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


# --- 計算補助関数 ---

def get_house_number(degree, cusps):
    """天体の度数からハウス番号を特定する"""
    # 13番目のカスプとして1番目のカスプを追加し、円環構造を扱う
    cusps_with_13th = list(cusps) + [cusps[0]]
    for i in range(12):
        start_cusp = cusps_with_13th[i]
        end_cusp = cusps_with_13th[i+1]
        # 0度をまたぐハウス(例: 350度から20度)の判定
        if start_cusp > end_cusp:
            if degree >= start_cusp or degree < end_cusp:
                return i + 1
        # 通常のハウスの判定
        else:
            if start_cusp <= degree < end_cusp:
                return i + 1
    return -1 # エラーケース

def find_solar_return_jd(birth_time_utc, natal_sun_lon, return_year):
    """ソーラーリターン（太陽回帰）の正確なユリウス日(UT)を計算する"""
    # おおよそのリターン日時を推測 (誕生日の年をリターン年に置き換える)
    guess_dt = birth_time_utc.replace(year=return_year)
    jd_ut, _ = swe.utc_to_jd(guess_dt.year, guess_dt.month, guess_dt.day, guess_dt.hour, guess_dt.minute, guess_dt.second, 1)

    # ニュートン法に似た反復計算で精度を高める (5回で十分収束)
    for _ in range(5):
        res = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)
        current_sun_lon = res[0][0]
        sun_speed = res[0][3]
        if sun_speed == 0: return None # 稀なエラーケース

        # ネイタル太陽との黄経差を計算
        offset = current_sun_lon - natal_sun_lon
        if offset > 180: offset -= 360
        if offset < -180: offset += 360

        # 黄経差と太陽の速度から時間的なズレを補正
        time_adjustment = -offset / sun_speed
        jd_ut += time_adjustment
    return jd_ut

# --- 天体データ計算・整形関数 ---

def calculate_celestial_points(jd_ut, lat, lon, is_helio=False):
    """指定されたユリウス日と場所の天体情報を計算して辞書で返す"""
    points = {}
    iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
    if is_helio:
        iflag |= swe.FLG_HELCTR
        celestial_bodies = HELIO_CELESTIAL_BODIES
    else:
        celestial_bodies = GEO_CELESTIAL_BODIES

    # 天体の位置計算
    for name, p_id in celestial_bodies.items():
        res = swe.calc_ut(jd_ut, p_id, iflag)
        pos = res[0][0]
        speed = res[0][3] if len(res[0]) > 3 else 0.0
        points[name] = {
            'id': p_id,
            'pos': pos,
            'is_retro': speed < 0,
            'speed': speed,
            'is_luminary': p_id in LUMINARIES or (is_helio and p_id == swe.EARTH)
        }

    # ハウスと感受点の計算 (ジオセントリックのみ)
    cusps, ascmc = None, None
    if not is_helio:
        try:
            cusps, ascmc = swe.houses(jd_ut, lat, lon, b'P')
            points["ASC"] = {'id': 'ASC', 'pos': ascmc[0], 'is_retro': False, 'speed': 0, 'is_luminary': True}
            points["MC"] = {'id': 'MC', 'pos': ascmc[1], 'is_retro': False, 'speed': 0, 'is_luminary': True}

            # パート・オブ・フォーチュン (PoF) の計算 (地平線基準)
            asc_pos = ascmc[0]
            dsc_pos = (asc_pos + 180) % ZODIAC_DEGREES
            sun_pos = points["太陽"]['pos']
            moon_pos = points["月"]['pos']

            is_night_birth = False
            if asc_pos < dsc_pos:
                if not (asc_pos <= sun_pos < dsc_pos): is_night_birth = True
            else: # 0度をまたぐ場合
                if dsc_pos <= sun_pos < asc_pos: is_night_birth = True

            if is_night_birth: # 夜生まれ
                pof_pos = (asc_pos + sun_pos - moon_pos + ZODIAC_DEGREES) % ZODIAC_DEGREES
            else: # 昼生まれ
                pof_pos = (asc_pos + moon_pos - sun_pos + ZODIAC_DEGREES) % ZODIAC_DEGREES
            points["PoF"] = {'id': 'PoF', 'pos': pof_pos, 'is_retro': False, 'speed': 0, 'is_luminary': False}

        except swe.Error as e:
            st.warning(f"ハウスが計算できませんでした（高緯度など）。ASC, MC, PoF, ハウスは表示されません。詳細: {e}")
            # 計算失敗時はNoneを返す
            return points, None, None

    return points, cusps, ascmc

def format_points_to_string_list(points, cusps, title):
    """計算された天体辞書を整形して文字列リストで返す"""
    lines = [f"\n🪐 ## {title} ##"]
    for name, data in points.items():
        pos = data['pos']
        sign_index = int(pos / DEGREES_PER_SIGN)
        degree = pos % DEGREES_PER_SIGN
        retro_info = "(R)" if data.get('is_retro', False) else ""
        
        house_info = ""
        if cusps and name not in SENSITIVE_POINTS:
            house_num = get_house_number(pos, cusps)
            house_info = f"(第{house_num}ハウス)"
        
        lines.append(f"{name:<12}: {SIGN_NAMES[sign_index]:<4} {degree:>5.2f}度 {retro_info:<3} {house_info}")
    return lines

def format_houses_to_string_list(cusps, title):
    """ハウスカスプ情報を整形して文字列リストで返す"""
    if cusps is None: return []
    lines = [f"\n🏠 ## {title} ##"]
    for i in range(12):
        pos = cusps[i]
        sign_index = int(pos / DEGREES_PER_SIGN)
        degree = pos % DEGREES_PER_SIGN
        lines.append(f"第{i+1:<2}ハウス: {SIGN_NAMES[sign_index]:<4} {degree:.2f}度")
    return lines

# --- アスペクト・ハーモニクス計算関数 ---

def calculate_aspects(points1, points2, prefix1, prefix2, results_list):
    """2つの天体群間のアスペクトを計算し、結果リストに追加する"""
    results_list.append(f"\n💫 ## {prefix1.strip('.')} - {prefix2.strip('.')} アスペクト ##")
    found_aspects = []
    p1_names, p2_names = list(points1.keys()), list(points2.keys())

    for i in range(len(p1_names)):
        for j in range(len(p2_names)):
            # 同じ天体群どうしの場合、重複ペアを除外 (例: 太陽-月 と 月-太陽)
            if points1 is points2 and i >= j:
                continue

            p1_name, p2_name = p1_names[i], p2_names[j]
            # PoFや感受点とマイナー天体のアスペクトは除外
            if (p1_name in SENSITIVE_POINTS and p2_name in ["ドラゴンヘッド", "リリス", "キロン"]) or \
               (p2_name in SENSITIVE_POINTS and p1_name in ["ドラゴンヘッド", "リリス", "キロン"]):
                continue

            p1, p2 = points1[p1_name], points2[p2_name]
            angle_diff = abs(p1['pos'] - p2['pos'])
            if angle_diff > 180:
                angle_diff = 360 - angle_diff

            for aspect_name, params in ASPECTS.items():
                is_luminary_involved = p1['is_luminary'] or p2['is_luminary']
                orb = params['orb_lum'] if is_luminary_involved else params['orb_other']
                
                current_orb = abs(angle_diff - params['angle'])
                if current_orb < orb:
                    line = f"{prefix1}{p1_name} - {prefix2}{p2_name}: {aspect_name} (オーブ {current_orb:.2f}度)"
                    found_aspects.append(line)

    if found_aspects:
        results_list.extend(found_aspects)
    else:
        results_list.append("設定されたオーブ内に主要なアスペクトは見つかりませんでした。")

def calculate_harmonic_conjunctions(natal_points, results_list):
    """ハーモニクスでコンジャンクションになるアスペクトを計算する"""
    results_list.append("\n" + "="*40)
    results_list.append("--- ハーモニクス ---")
    results_list.append("\n🎵 ## ハーモニクスでコンジャンクションになるアスペクト ##")
    found_harmonics = []
    p_names = list(natal_points.keys())

    for i in range(len(p_names)):
        for j in range(i + 1, len(p_names)):
            p1_name, p2_name = p_names[i], p_names[j]
            # 感受点と特定天体の組み合わせを除外
            if (p1_name in SENSITIVE_POINTS and p2_name in ["ドラゴンヘッド", "リリス", "キロン"]) or \
               (p2_name in SENSITIVE_POINTS and p1_name in ["ドラゴンヘッド", "リリス", "キロン"]):
                continue

            p1, p2 = natal_points[p1_name], natal_points[p2_name]
            angle = abs(p1['pos'] - p2['pos'])
            if angle > 180: angle = 360 - angle
            if angle < 1.0: continue # コンジャンクションは除外

            for n in TARGET_HARMONICS:
                harmonic_angle = (angle * n) % 360
                if harmonic_angle < HARMONIC_ORB or harmonic_angle > (360 - HARMONIC_ORB):
                    line = f"N.{p1_name} - N.{p2_name} (約 {angle:.1f}度) は **H{n}** でコンジャンクションになります。"
                    found_harmonics.append(line)

    if found_harmonics:
        results_list.extend(found_harmonics)
    else:
        results_list.append("指定されたハーモニクス数でコンジャンクションになるアスペクトは見つかりませんでした。")


# --- Streamlit UI設定 ---
st.set_page_config(page_title="西洋占星術カリキュレータ", page_icon="🪐", layout="wide")
st.title("🪐 西洋占星術カリキュレータ")
st.write("出生情報と現在の滞在場所を入力して、ホロスコープを計算します。")
st.info("**【重要】** 現在、時刻は**日本標準時(JST, UTC+9)**として扱われます。海外で生まれた方は、出生時刻を一度JSTに換算して入力するか、UTCで入力し、経度からタイムゾーンを計算できるツールをご利用ください。")


# --- UI入力欄 ---
use_manual_coords_birth = st.checkbox("出生地が海外 / 緯度経度を直接入力する", key="manual_birth")
use_manual_coords_sr = st.checkbox("ソーラーリターン用の滞在場所が海外 / 緯度経度を直接入力する", key="manual_sr")
st.markdown("---")

with st.form(key='birth_info_form'):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("出生情報")
        birth_date = st.date_input("📅 生年月日", min_value=datetime(1900, 1, 1), max_value=datetime.now(), value=datetime(1976, 12, 25))
        time_str = st.text_input("⏰ 出生時刻 (24時間表記)", value="16:25")
        
        selected_prefecture = st.selectbox("📍 出生都道府県", options=list(prefecture_data.keys()), index=12, disabled=use_manual_coords_birth)
        b_col1, b_col2 = st.columns(2)
        birth_lat = b_col1.number_input("出生地の緯度 (北緯+, 南緯-)", -90.0, 90.0, 35.690, format="%.4f", disabled=not use_manual_coords_birth)
        birth_lon = b_col2.number_input("出生地の経度 (東経+, 西経-)", -180.0, 180.0, 139.692, format="%.4f", disabled=not use_manual_coords_birth)

    with col2:
        st.subheader("ソーラーリターン用の情報")
        return_year = st.number_input("ソーラーリターンを計算する年", min_value=1900, max_value=2100, value=datetime.now().year)
        
        sr_prefecture = st.selectbox("📍 滞在場所（都道府県）", options=list(prefecture_data.keys()), index=12, disabled=use_manual_coords_sr)
        sr_col1, sr_col2 = st.columns(2)
        sr_lat_input = sr_col1.number_input("滞在場所の緯度 (北緯+, 南緯-)", -90.0, 90.0, 35.690, format="%.4f", disabled=not use_manual_coords_sr)
        sr_lon_input = sr_col2.number_input("滞在場所の経度 (東経+, 西経-)", -180.0, 180.0, 139.692, format="%.4f", disabled=not use_manual_coords_sr)

    submit_button = st.form_submit_button(label='ホロスコープを計算する ✨')

# --- 計算実行 ---
if submit_button:
    try:
        birth_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        st.error("時刻の形式が正しくありません。「HH:MM」（例: 16:25）の形式で入力してください。")
        st.stop()

    results_to_copy = []
    
    try:
        # --- 基礎データ準備 ---
        # 天体暦ファイルの設定
        ephe_path = 'ephe'
        if not os.path.exists(ephe_path):
            st.error(f"天体暦ファイルが見つかりません。'{ephe_path}' フォルダを配置してください。")
            st.stop()
        swe.set_ephe_path(ephe_path)

        # 出生時刻をUTCに変換 (入力はJSTとみなす)
        user_birth_time_local = datetime.combine(birth_date, birth_time)
        jst = timezone(timedelta(hours=9))
        # ▼▼▼【エラー修正】 'localize' を 'replace' に変更 ▼▼▼
        birth_time_utc = user_birth_time_local.replace(tzinfo=jst).astimezone(timezone.utc)
        
        # UTとETのユリウス日を取得
        jd_ut_natal, jd_et_natal = swe.utc_to_jd(birth_time_utc.year, birth_time_utc.month, birth_time_utc.day, birth_time_utc.hour, birth_time_utc.minute, birth_time_utc.second, 1)

        # 出生地の緯度経度を取得
        if use_manual_coords_birth:
            lat, lon = birth_lat, birth_lon
            birth_location_name = f"緯度:{lat:.3f}, 経度:{lon:.3f}"
        else:
            coords = prefecture_data[selected_prefecture]
            lat, lon = coords["lat"], coords["lon"]
            birth_location_name = selected_prefecture
        
        progressed_days = (datetime.now(timezone.utc).date() - birth_time_utc.date()).days
        age = int(progressed_days / 365.25) # 参考用の満年齢

        header_str = f"✨ {birth_date.year}年{birth_date.month}月{birth_date.day}日 {birth_time.strftime('%H:%M')}生 ({birth_location_name}) - 年齢: {age}歳"
        st.header(header_str)
        results_to_copy.append(header_str)

        # --- 1. ネイタルチャート計算 (ジオセントリック) ---
        with st.spinner("ジオセントリック（ネイタル）を計算中..."):
            results_to_copy.append("\n" + "="*40); results_to_copy.append("--- ジオセントリック (ネイタル) ---")
            natal_points, natal_cusps, _ = calculate_celestial_points(jd_ut_natal, lat, lon)
            results_to_copy.extend(format_points_to_string_list(natal_points, natal_cusps, "ネイタルチャート"))
            results_to_copy.extend(format_houses_to_string_list(natal_cusps, "ハウス (ネイタル)"))
            calculate_aspects(natal_points, natal_points, "N.", "N.", results_to_copy)

        # --- 2. ネイタルチャート計算 (ヘリオセントリック) ---
        with st.spinner("ヘリオセントリックを計算中..."):
            results_to_copy.append("\n" + "="*40); results_to_copy.append("--- ヘリオセントリック (ネイタル) ---")
            helio_points, _, _ = calculate_celestial_points(jd_ut_natal, lat, lon, is_helio=True)
            results_to_copy.extend(format_points_to_string_list(helio_points, None, "ネイタルチャート (ヘリオ)"))
            calculate_aspects(helio_points, helio_points, "H.", "H.", results_to_copy)

        # --- 3. トランジット情報 ---
        with st.spinner("トランジットを計算中..."):
            results_to_copy.append("\n" + "="*40); results_to_copy.append("--- トランジット ---")
            transit_dt_utc = datetime.now(timezone.utc)
            jd_ut_transit, _ = swe.utc_to_jd(transit_dt_utc.year, transit_dt_utc.month, transit_dt_utc.day, transit_dt_utc.hour, transit_dt_utc.minute, transit_dt_utc.second, 1)
            transit_points, _, _ = calculate_celestial_points(jd_ut_transit, lat, lon) # トランジットのハウスは通常見ないので緯度経度はネイタルを使用
            calculate_aspects(transit_points, natal_points, "T.", "N.", results_to_copy)

        # --- 4. プログレス情報 (一日一年法) ---
        with st.spinner("プログレスを計算中..."):
            results_to_copy.append("\n" + "="*40); results_to_copy.append(f"--- プログレス (出生後{progressed_days}日目) ---")
            prog_dt_utc = birth_time_utc + timedelta(days=progressed_days)
            jd_ut_prog, _ = swe.utc_to_jd(prog_dt_utc.year, prog_dt_utc.month, prog_dt_utc.day, prog_dt_utc.hour, prog_dt_utc.minute, prog_dt_utc.second, 1)
            progressed_points, _, _ = calculate_celestial_points(jd_ut_prog, lat, lon)
            # プログレスでは通常、主要7天体+キロンなどを見るため、表示を絞ることも可能
            calculate_aspects(progressed_points, natal_points, "P.", "N.", results_to_copy)

        # --- 5. ソーラーアーク情報 ---
        with st.spinner("ソーラーアークを計算中..."):
            results_to_copy.append("\n" + "="*40); results_to_copy.append("--- ソーラーアーク ---")
            progressed_sun_pos = progressed_points["太陽"]['pos']
            natal_sun_pos = natal_points["太陽"]['pos']
            solar_arc = (progressed_sun_pos - natal_sun_pos + ZODIAC_DEGREES) % ZODIAC_DEGREES
            
            solar_arc_points = {}
            for name, data in natal_points.items():
                if name == "PoF": continue # PoFは通常アークさせない
                sa_pos = (data['pos'] + solar_arc) % ZODIAC_DEGREES
                solar_arc_points[name] = {'id': data['id'], 'pos': sa_pos, 'is_luminary': data['is_luminary']}
            calculate_aspects(solar_arc_points, natal_points, "SA.", "N.", results_to_copy)

        # --- 6. ソーラーリターン情報 ---
        with st.spinner("ソーラーリターンを計算中..."):
            natal_sun_lon = natal_points["太陽"]['pos']
            jd_solar_return_ut = find_solar_return_jd(birth_time_utc, natal_sun_lon, return_year)
            
            if jd_solar_return_ut is None:
                st.error("ソーラーリターンの計算に失敗しました。")
            else:
                results_to_copy.append("\n" + "="*40)
                # SR用の緯度経度を取得
                if use_manual_coords_sr:
                    sr_lat, sr_lon = sr_lat_input, sr_lon_input
                    sr_location_name = f"緯度:{sr_lat:.3f}, 経度:{sr_lon:.3f}"
                else:
                    sr_coords = prefecture_data[sr_prefecture]
                    sr_lat, sr_lon = sr_coords["lat"], sr_coords["lon"]
                    sr_location_name = sr_prefecture

                # UTをJSTに変換して表示
                y, m, d, h_decimal = swe.revjul(jd_solar_return_ut, swe.GREG_CAL)
                sr_dt_utc = datetime.fromtimestamp(swe.julday(y, m, d, h_decimal), tz=timezone.utc)
                sr_dt_local = sr_dt_utc.astimezone(jst)

                sr_header = f"🎂 ## {return_year}年 ソーラーリターンチャート ##\n({sr_dt_local.strftime('%Y-%m-%d %H:%M:%S')} @ {sr_location_name})"
                results_to_copy.append(sr_header)
                
                sr_points, sr_cusps, _ = calculate_celestial_points(jd_solar_return_ut, sr_lat, sr_lon)
                results_to_copy.extend(format_points_to_string_list(sr_points, sr_cusps, "惑星のサイン (ソーラーリターン)"))
                results_to_copy.extend(format_houses_to_string_list(sr_cusps, "ハウス (ソーラーリターン)"))
                calculate_aspects(sr_points, sr_points, "SR.", "SR.", results_to_copy)
                calculate_aspects(sr_points, natal_points, "SR.", "N.", results_to_copy) # リターンとネイタルの二重円

        # --- 7. ハーモニクス情報 ---
        with st.spinner("ハーモニクスを計算中..."):
            calculate_harmonic_conjunctions(natal_points, results_to_copy)

        # --- 最終結果の表示 ---
        st.success("全ての計算が完了しました。")
        final_results_string = "\n".join(results_to_copy)
        st.code(final_results_string, language=None)

    except Exception as e:
        st.error(f"計算中に予期せぬエラーが発生しました。入力値が適切かご確認ください。")
        st.exception(e)

