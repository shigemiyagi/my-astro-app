import streamlit as st
import swisseph as swe
from datetime import datetime, timezone, timedelta
import os

# --- 関数定義 ---
# (get_house_number関数は元のコードと同じなので省略)
def get_house_number(degree, cusps):
    """度数からハウス番号を特定する"""
    cusps_with_13th = list(cusps) + [cusps[0]]
    for i in range(12):
        start_cusp = cusps_with_13th[i]
        end_cusp = cusps_with_13th[i+1]
        if start_cusp > end_cusp:
            if degree >= start_cusp or degree < end_cusp:
                return i + 1
        else:
            if start_cusp <= degree < end_cusp:
                return i + 1
    return -1

# --- Streamlit UI設定 ---
st.set_page_config(page_title="My占星術ホロスコープ", page_icon="🪐")
st.title("🪐 西洋占星術ホロスコープ作成")
st.write("あなたの出生情報を入力して、ホロスコープを作成します。")

# --- 入力フォーム ---
with st.form(key='birth_info_form'):
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input("📅 生年月日", min_value=datetime(1900, 1, 1), max_value=datetime.now(), value=datetime(1990, 1, 1))
        lon = st.number_input("🌏 出生地の経度 (東経はプラス)", value=139.76, format="%.4f")
        
    with col2:
        birth_time = st.time_input("⏰ 生まれた時刻", value=datetime(1990, 1, 1, 12, 0).time())
        lat = st.number_input("🌏 出生地の緯度 (北緯はプラス)", value=35.68, format="%.4f")

    tz_hour = st.number_input("🕒 出生地のタイムゾーン (日本は「9」)", value=9)
    
    submit_button = st.form_submit_button(label='ホロスコープを作成する ✨')

# --- ボタンが押されたら計算を実行 ---
if submit_button:
    # --- 正確なユリウス日を計算 ---
    year, month, day = birth_date.year, birth_date.month, birth_date.day
    hour, minute = birth_time.hour, birth_time.minute
    
    user_birth_time = datetime(year, month, day, hour, minute)
    user_timezone = timezone(timedelta(hours=tz_hour))
    birth_time_aware = user_birth_time.replace(tzinfo=user_timezone)
    birth_time_utc = birth_time_aware.astimezone(timezone.utc)
    jd_et = swe.utc_to_jd(
        birth_time_utc.year, birth_time_utc.month, birth_time_utc.day,
        birth_time_utc.hour, birth_time_utc.minute, birth_time_utc.second,
        1
    )[1]

    # --- スイスエフェメリス設定 ---
    # プロジェクト内の 'ephe' フォルダを指定
    ephe_path = 'ephe'
    if not os.path.exists(ephe_path):
        st.error(f"天体暦ファイルが見つかりません。'{ephe_path}' フォルダを配置してください。")
        st.stop()
    swe.set_ephe_path(ephe_path)
    h_sys = b'P'

    # --- 定数リスト --- (元のコードと同じ)
    celestial_ids = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO, swe.CHIRON, swe.MEAN_NODE, swe.MEAN_APOG]
    celestial_names = ["太陽", "月", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星", "キロン", "ドラゴンヘッド", "リリス"]
    sign_names = ["牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座", "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"]
    aspect_names = {0: "コンジャンクション (0度)", 60: "セクスタイル (60度)", 90: "スクエア (90度)", 120: "トライン (120度)", 180: "オポジション (180度)"}
    MAJOR_ASPECT_ORB_LUMINARIES = 8
    MAJOR_ASPECT_ORB_OTHERS = 6
    SEXTILE_ORB = 3

    # --- 計算と結果の保存 ---
    celestial_points = {}
    iflag = swe.FLG_SWIEPH | swe.FLG_SPEED

    cusps, ascmc = swe.houses(jd_et, lat, lon, h_sys)
    asc_pos, mc_pos = ascmc[0], ascmc[1]

    for i, p_id in enumerate(celestial_ids):
        if p_id == swe.MEAN_APOG:
            xx, ret = swe.calc(jd_et, p_id, iflag)
        else:
            xx, ret = swe.calc_ut(jd_et, p_id, iflag)
        pos, speed = xx[0], xx[3]
        celestial_points[celestial_names[i]] = {'id': p_id, 'pos': pos, 'is_retro': speed < 0, 'speed': speed, 'is_luminary': p_id in [swe.SUN, swe.MOON]}

    celestial_points["ASC"] = {'id': 'ASC', 'pos': asc_pos, 'is_retro': False, 'speed': 0, 'is_luminary': True}
    celestial_points["MC"] = {'id': 'MC', 'pos': mc_pos, 'is_retro': False, 'speed': 0, 'is_luminary': True}
    pof_pos = (asc_pos + celestial_points["月"]['pos'] - celestial_points["太陽"]['pos']) % 360
    celestial_points["PoF"] = {'id': 'PoF', 'pos': pof_pos, 'is_retro': False, 'speed': 0, 'is_luminary': False}

    # --- 結果の表示 ---
    st.markdown("---")
    st.header("✨ 占星術情報")

    st.subheader("🪐 惑星と感受点のサイン")
    for name, data in celestial_points.items():
        pos, sign_index, degree = data['pos'], int(data['pos'] / 30), data['pos'] % 30
        retro_info = "(R)" if data['is_retro'] else ""
        house_num = get_house_number(pos, cusps)
        st.text(f"{name:<12}: {sign_names[sign_index]:<4} {degree:>5.2f}度 {retro_info:<3} (第{house_num}ハウス)")

    st.subheader("🏠 ハウス")
    for i in range(12):
        sign_index, degree = int(cusps[i] / 30), cusps[i] % 30
        st.text(f"第{i+1:<2}ハウス: {sign_names[sign_index]:<4} {degree:.2f}度")

    st.subheader("💫 アスペクト")
    # (アスペクト計算と表示のロジックは元のコードと同じ)
    found_aspects = False
    point_names = list(celestial_points.keys())
    for i in range(len(point_names)):
        for j in range(i + 1, len(point_names)):
            p1_name, p2_name = point_names[i], point_names[j]
            if p1_name in ["ドラゴンヘッド", "リリス", "キロン"] and p2_name in ["ASC", "MC", "PoF"]: continue
            if p2_name in ["ドラゴンヘッド", "リリス", "キロン"] and p1_name in ["ASC", "MC", "PoF"]: continue
            p1, p2 = celestial_points[p1_name], celestial_points[p2_name]
            is_major_point_involved = p1['is_luminary'] or p2['is_luminary']
            angle = abs(p1['pos'] - p2['pos'])
            if angle > 180: angle = 360 - angle
            for aspect_angle, aspect_name in aspect_names.items():
                orb = 0
                if aspect_angle in [0, 90, 120, 180]:
                    orb = MAJOR_ASPECT_ORB_LUMINARIES if is_major_point_involved else MAJOR_ASPECT_ORB_OTHERS
                elif aspect_angle == 60:
                    orb = SEXTILE_ORB
                current_orb = abs(angle - aspect_angle)
                if 0 < orb and current_orb < orb:
                    st.text(f"{p1_name} - {p2_name}: {aspect_name} (オーブ {current_orb:.2f}度)")
                    found_aspects = True
    if not found_aspects:
        st.write("設定されたオーブ内に主要なアスペクトは見つかりませんでした。")
