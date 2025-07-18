import streamlit as st
import swisseph as swe
from datetime import datetime, timezone, timedelta
import os

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

# --- 関数定義 ---
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
st.set_page_config(page_title="西洋占星術カリキュレータ", page_icon="🪐")
st.title("🪐 西洋占星術カリキュレータ")
st.write("出生情報を入力して、ホロスコープを計算します。")

# --- 入力フォーム ---
with st.form(key='birth_info_form'):
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input("📅 生年月日", min_value=datetime(1900, 1, 1), max_value=datetime.now(), value=datetime(1976, 12, 25))
        
    with col2:
        time_str = st.text_input("⏰ 出生時刻 (24時間形式）", value="16:25")

    selected_prefecture = st.selectbox("📍 出生都道府県", options=list(prefecture_data.keys()))
    
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
    tz_hour = 9
    coords = prefecture_data[selected_prefecture]
    lat, lon = coords["lat"], coords["lon"]
    
    user_birth_time = datetime(year, month, day, hour, minute)
    user_timezone = timezone(timedelta(hours=tz_hour))
    birth_time_aware = user_birth_time.replace(tzinfo=user_timezone)
    birth_time_utc = birth_time_aware.astimezone(timezone.utc)
    jd_et = swe.utc_to_jd(
        birth_time_utc.year, birth_time_utc.month, birth_time_utc.day,
        birth_time_utc.hour, birth_time_utc.minute, birth_time_utc.second,
        1
    )[1]

    ephe_path = 'ephe'
    if not os.path.exists(ephe_path):
        st.error(f"天体暦ファイルが見つかりません。'{ephe_path}' フォルダを配置してください。")
        st.stop()
    swe.set_ephe_path(ephe_path)
    h_sys = b'P'

    # --- 定数リスト ---
    celestial_ids = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO, swe.CHIRON, swe.MEAN_NODE, swe.MEAN_APOG]
    celestial_names = ["太陽", "月", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星", "キロン", "ドラゴンヘッド", "リリス"]
    sign_names = ["牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座", "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"]
    aspect_names = {0: "コンジャンクション (0度)", 60: "セクスタイル (60度)", 90: "スクエア (90度)", 120: "トライン (120度)", 180: "オポジション (180度)"}
    MAJOR_ASPECT_ORB_LUMINARIES, MAJOR_ASPECT_ORB_OTHERS, SEXTILE_ORB = 8, 6, 3

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
    # ▼▼▼ 修正点：結果をリストに貯めてから最後に出力する ▼▼▼
    results_to_copy = []
    
    header_str = f"✨ {birth_date.year}年{birth_date.month}月{birth_date.day}日 {birth_time.strftime('%H:%M')}生 ({selected_prefecture})"
    st.header(header_str)
    results_to_copy.append(header_str)
    results_to_copy.append("-" * 40) # 区切り線

    # 惑星と感受点のサイン
    results_to_copy.append("\n🪐 ## 惑星と感受点のサイン ##")
    for name, data in celestial_points.items():
        pos, sign_index, degree = data['pos'], int(data['pos'] / 30), data['pos'] % 30
        retro_info = "(R)" if data['is_retro'] else ""
        house_num = get_house_number(pos, cusps)
        line = f"{name:<12}: {sign_names[sign_index]:<4} {degree:>5.2f}度 {retro_info:<3} (第{house_num}ハウス)"
        results_to_copy.append(line)

    # ハウス
    results_to_copy.append("\n🏠 ## ハウス ##")
    for i in range(12):
        sign_index, degree = int(cusps[i] / 30), cusps[i] % 30
        line = f"第{i+1:<2}ハウス: {sign_names[sign_index]:<4} {degree:.2f}度"
        results_to_copy.append(line)

    # アスペクト
    results_to_copy.append("\n💫 ## アスペクト ##")
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
                    line = f"{p1_name} - {p2_name}: {aspect_name} (オーブ {current_orb:.2f}度)"
                    results_to_copy.append(line)
                    found_aspects = True
    if not found_aspects:
        results_to_copy.append("設定されたオーブ内に主要なアスペクトは見つかりませんでした。")

    # --- コピー用のテキストエリアに全結果を表示 ---
    final_results_string = "\n".join(results_to_copy)
    st.code(final_results_string, language=None)
