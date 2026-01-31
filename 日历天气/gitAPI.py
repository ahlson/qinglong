import requests
import pymysql
import logging
from pymysql.constants import CLIENT
from datetime import datetime, timezone, timedelta
import os
import cryptography

# ===================== 环境变量配置 =====================
# MySQL 数据库地址（IP 或域名）
MYL_HOST = os.getenv("MYL_HOST", "").strip()

# MySQL 端口号（环境变量读取后需显式转换为 int）
MYL_PORT = int(os.getenv("MYL_PORT", "").strip())

# MySQL 登录用户名
MYL_USER = os.getenv("MYL_USER", "").strip()

# MySQL 登录密码
MYL_PASS = os.getenv("MYL_PASS", "").strip()

# 日历 API 的 App ID（第三方服务认证信息）
APP_ID = os.getenv("APP_ID", "").strip()

# 日历 API 的 App Secret（第三方服务认证信息）
APP_SECRET = os.getenv("APP_SECRET", "").strip()

# 天气 API Key（用于和风天气等服务的鉴权）
API_key = os.getenv("API_key", "").strip()

# 天气查询城市 / 地区编码（如城市 ID、Location Code）
LOCATION = os.getenv("LOCATION", "").strip()

# ===================== 全局配置 =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("calendar_weather_hitokoto")

DB_CONFIG = {
    'host': MYL_HOST,
    'port': MYL_PORT,
    'user': MYL_USER,
    'password': MYL_PASS,
    'database': 'rili',
    'client_flag': CLIENT.MULTI_STATEMENTS
}

API_CONFIG = {
    "calendar": {
        "url_template": "http://www.mxnzp.com/api/holiday/list/month/{month}",
        "headers": {
            'app_id': APP_ID,
            'app_secret': APP_SECRET
        }
    },
    "weather": {
        "api_key": API_key,
        "location": LOCATION,  # 郑州气象API城市ID
        "now_url": "https://pm6vhfyu8v.re.qweatherapi.com/v7/weather/now",
        "3d_url": "https://pm6vhfyu8v.re.qweatherapi.com/v7/weather/3d"
    },
    "hitokoto": {
        "url": "https://v1.hitokoto.cn/?max_length=22"
    }
}


# ===================== 公共工具类 =====================
class DBUtil:
    """数据库工具类（封装公共数据库操作）"""

    @staticmethod
    def get_connection():
        try:
            conn = pymysql.connect(**DB_CONFIG)
            logger.info("数据库连接成功")
            return conn
        except pymysql.Error as e:
            logger.error(f"数据库连接失败: {e}")
            return None

    @staticmethod
    def close_connection(conn):
        if conn and conn.open:
            try:
                conn.close()
                logger.info("数据库连接已关闭")
            except pymysql.Error as e:
                logger.error(f"关闭数据库连接失败: {e}")

    @staticmethod
    def execute_sql(conn, sql, params=None, commit=False):
        if not conn:
            logger.error("数据库连接为空，无法执行SQL")
            return None, 0

        cursor = None
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            result = cursor.fetchall() if not commit else None
            row_count = cursor.rowcount

            if commit:
                conn.commit()
                logger.info(f"SQL执行成功，影响行数: {row_count}")
            return result, row_count
        except pymysql.Error as e:
            logger.error(f"SQL执行失败: {e}, SQL: {sql}, 参数: {params}")
            if commit:
                conn.rollback()
            return None, 0
        finally:
            if cursor:
                cursor.close()


class DateUtil:
    """日期时间工具类"""

    @staticmethod
    def convert_time_format(time_str):
        """将 2026-01-30T15:16+08:00 → 2026-01-30 15:16:00"""
        try:
            time_str = time_str.replace("T", " ").split("+")[0]
            if len(time_str.split(":")) == 2:
                time_str += ":00"
            return time_str
        except Exception as e:
            logger.error(f"时间格式转换失败: {e}，使用当前时间替代")
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_weekday(date_str):
        """输入 yyyy-mm-dd，输出中文周几"""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            weekday_map = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
            return weekday_map[dt.weekday()]
        except Exception as e:
            logger.error(f"周几转换失败（date={date_str}）：{e}")
            return "未知"

    @staticmethod
    def convert_weekday_num_to_cn(weekday_num):
        """将weekDay原始数字（1-7）转换为汉字（周一到周日）"""
        weekday_map = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}
        try:
            num = int(weekday_num)
            return weekday_map.get(num, "未知")
        except (ValueError, TypeError):
            logger.warning(f"星期数字转换失败，原始值：{weekday_num}")
            return "未知"

    @staticmethod
    def get_current_month():
        """获取当前月份，格式为 YYYYMM（如 202601）"""
        try:
            current_month = datetime.now().strftime("%Y%m")
            logger.info(f"自动获取当前月份：{current_month}")
            return current_month
        except Exception as e:
            logger.error(f"获取当前月份失败，默认使用上月: {e}")
            last_month = datetime.now() - timedelta(days=datetime.now().day)
            return last_month.strftime("%Y%m")

    @staticmethod
    def convert_lunar_to_4chars(lunar_str):
        """
        转换农历文本为固定4个汉字，核心规则：
        1. 20号统一显示为「二十」、30号统一显示为「三十」（保证4字）
        2. 21-29号显示为「廿一~廿九」、31号显示为「卅一」（本身凑4字）
        3. 1-9号显示为「初一~初九」、10-19号显示为「初十~十九」（凑4字）
        """
        if not isinstance(lunar_str, str) or not lunar_str:
            return lunar_str

        # 定义农历月份关键词
        lunar_months = ["正月", "二月", "三月", "四月", "五月", "六月",
                        "七月", "八月", "九月", "十月", "冬月", "腊月"]
        month_part = ""
        day_part = ""

        # 拆分月份和日期
        for m in lunar_months:
            if lunar_str.startswith(m):
                month_part = m
                day_part = lunar_str[len(m):].strip()
                break

        # 未匹配到标准月份的兜底处理
        if not month_part:
            logger.warning(f"无法识别农历月份：{lunar_str}，直接返回原字符串（截断/补全为4字）")
            return lunar_str[:4] if len(lunar_str) >= 4 else lunar_str.ljust(4, "　")

        # 核心日期转换规则（确保最终拼接后是4字）
        day_replace_rules = {
            # 1-9号：补"初"
            "一": "初一", "二": "初二", "三": "初三", "四": "初四", "五": "初五",
            "六": "初六", "七": "初七", "八": "初八", "九": "初九",
            # 10-19号：补"初"（10号特殊为"初十"）
            "十": "初十", "十一": "十一", "十二": "十二", "十三": "十三", "十四": "十四",
            "十五": "十五", "十六": "十六", "十七": "十七", "十八": "十八", "十九": "十九",
            # 20号：统一为"二十"（关键修正）
            "二十": "二十", "廿十": "二十", "廿": "二十",
            # 21-29号：保持"廿一~廿九"
            "二十一": "廿一", "廿一": "廿一", "二十二": "廿二", "廿二": "廿二",
            "二十三": "廿三", "廿三": "廿三", "二十四": "廿四", "廿四": "廿四",
            "二十五": "廿五", "廿五": "廿五", "二十六": "廿六", "廿六": "廿六",
            "二十七": "廿七", "廿七": "廿七", "二十八": "廿八", "廿八": "廿八",
            "二十九": "廿九", "廿九": "廿九",
            # 30号：统一为"三十"（关键修正）
            "三十": "三十", "卅": "三十",
            # 31号：保持"卅一"
            "三十一": "卅一", "卅一": "卅一"
        }

        # 转换日期部分（优先匹配精准值，无匹配则保留原日期）
        converted_day = day_replace_rules.get(day_part, day_part)

        # 拼接并强制保证4字长度
        final_lunar = month_part + converted_day
        # 极端情况容错：长度不足补全角空格，过长截取前4字
        if len(final_lunar) < 4:
            final_lunar = final_lunar.ljust(4, "　")  # 全角空格避免显示错位
        elif len(final_lunar) > 4:
            final_lunar = final_lunar[:4]

        # 调试日志
        if final_lunar != lunar_str:
            logger.debug(f"农历转换完成：{lunar_str} → {final_lunar}（4字）")

        return final_lunar


class ApiUtil:
    """API请求工具类"""

    @staticmethod
    def send_get_request(url, headers=None, timeout=10):
        try:
            response = requests.get(url, headers=headers or {}, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"API请求成功: {url}")
            return result
        except requests.exceptions.HTTPError as e:
            logger.error(f"API HTTP错误: {e}, URL: {url}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"API连接错误: {e}, URL: {url}")
        except requests.exceptions.Timeout as e:
            logger.error(f"API超时错误: {e}, URL: {url}")
        except ValueError as e:
            logger.error(f"API返回非JSON格式: {e}, URL: {url}")
        except Exception as e:
            logger.error(f"API请求未知错误: {e}, URL: {url}")
        return None


# ===================== 业务逻辑模块 =====================
class CalendarHandler:
    """日历数据处理模块"""

    @staticmethod
    def format_type_des_for_today(item):
        """仅适配today表：detailsType=3时返回typeDes，其余为空"""
        if item.get('detailsType') == 3:
            return item.get('typeDes', '').strip() or ''
        return ''

    @staticmethod
    def format_type_des_for_rlibiao(item):
        """rlibiao表原始逻辑：完全保留原有规则"""
        if item['type'] == 2:
            if item['detailsType'] == 3:
                return item['typeDes']
            elif item['detailsType'] == 2:
                return "休息日"
        return item['typeDes']

    @staticmethod
    def format_suit_avoid(original_text):
        """处理宜/忌字段格式"""
        text = original_text.strip()
        if not text:
            return "无"

        parts = text.split('.')
        valid_parts = [part.strip() for part in parts if part.strip()]
        if not valid_parts:
            return "无"

        result = []
        current_total_length = 0
        for part in valid_parts:
            separator_length = 1 if result else 0
            total_length_after_add = current_total_length + len(part) + separator_length
            if total_length_after_add <= 26:
                result.append(part)
                current_total_length = total_length_after_add
            else:
                break

        final_text = '·'.join(result)
        return final_text if final_text else "无"

    @staticmethod
    def get_calendar_data(month=None):
        """获取日历接口数据（默认使用当月）"""
        target_month = month or DateUtil.get_current_month()
        config = API_CONFIG["calendar"]
        url = config["url_template"].format(month=target_month)
        return ApiUtil.send_get_request(url, config["headers"])

    @staticmethod
    def insert_rlibiao(data, conn):
        """插入日历表数据（完全还原原始逻辑，无任何修改）"""
        if not data:
            logger.warning("无日历数据，跳过rlibiao表插入")
            return

        insert_count = 0
        for item in data:
            # 检查重复
            check_sql = "SELECT 1 FROM rlibiao WHERE date = %s"
            check_result, _ = DBUtil.execute_sql(conn, check_sql, (item['date'],))
            if check_result:
                continue

            # 处理字段：完全还原原始逻辑
            adjusted_type_des = CalendarHandler.format_type_des_for_rlibiao(item)
            lunar_calendar = DateUtil.convert_lunar_to_4chars(item['lunarCalendar'])

            # 插入数据：完全还原原始参数
            insert_sql = """
            INSERT INTO rlibiao (date, weekDay, lunarCalendar, typeDes, type)
            VALUES (%s, %s, %s, %s, %s)
            """
            _, row_count = DBUtil.execute_sql(
                conn, insert_sql,
                (item['date'], item['weekDay'], lunar_calendar, adjusted_type_des, item['type']),
                commit=True
            )
            insert_count += row_count

        logger.info(f"日历表rlibiao：新增插入 {insert_count} 条数据，其余为重复数据")

    @staticmethod
    def insert_today(data, conn):
        """仅修改today表：typeDes（detailsType=3赋值）+ weekDay数字转汉字"""
        if not data:
            logger.warning("无日历数据，跳过today表插入")
            return

        insert_count = 0
        for item in data:
            # 检查重复
            check_sql = "SELECT 1 FROM today WHERE today = %s"
            check_result, _ = DBUtil.execute_sql(conn, check_sql, (item['date'],))
            if check_result:
                continue

            # 处理字段
            year_tips = f"{item['yearTips']}【{item['chineseZodiac']}】年"
            suit = CalendarHandler.format_suit_avoid(item['suit'])
            avoid = CalendarHandler.format_suit_avoid(item['avoid'])
            lunar_calendar = DateUtil.convert_lunar_to_4chars(item['lunarCalendar'])
            # today表专属：仅detailsType=3时赋值typeDes
            type_des = CalendarHandler.format_type_des_for_today(item)
            # today表专属：weekDay数字转汉字
            weekday_cn = DateUtil.convert_weekday_num_to_cn(item.get('weekDay'))

            # 插入数据（新增typeDes字段，weekDay用转换后的汉字）
            insert_sql = """
            INSERT INTO today (today, yearTips, weekDay, lunarCalendar, suit, avoid, uptime, typeDes)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
            """
            _, row_count = DBUtil.execute_sql(
                conn, insert_sql,
                (item['date'], year_tips, weekday_cn, lunar_calendar, suit, avoid, type_des),
                commit=True
            )
            insert_count += row_count

        logger.info(f"当日表today：新增插入 {insert_count} 条数据，其余为重复数据")

    @classmethod
    def process_calendar(cls, month=None):
        """处理日历数据主流程（无修改）"""
        logger.info("===== 开始处理日历数据 =====")
        raw_data = cls.get_calendar_data(month)
        if not raw_data or raw_data.get("code") != 1:
            logger.error("获取日历接口数据失败")
            return

        calendar_data = raw_data.get("data", [])
        if not calendar_data:
            logger.warning("日历接口返回空数据")
            return

        conn = DBUtil.get_connection()
        if not conn:
            return

        try:
            cls.insert_rlibiao(calendar_data, conn)
            cls.insert_today(calendar_data, conn)
            logger.info("日历数据处理完成")
        finally:
            DBUtil.close_connection(conn)


class WeatherHandler:
    """天气数据处理模块（完全未动）"""

    @staticmethod
    def get_weather_now():
        """获取实时天气数据"""
        config = API_CONFIG["weather"]
        url = f"{config['now_url']}?location={config['location']}"
        headers = {'X-QW-Api-Key': config['api_key']}
        data = ApiUtil.send_get_request(url, headers)
        return data["now"] if data and data.get("code") == "200" else None

    @staticmethod
    def get_3d_forecast():
        """获取3天预报数据"""
        config = API_CONFIG["weather"]
        url = f"{config['3d_url']}?location={config['location']}"
        headers = {'X-QW-Api-Key': config['api_key']}
        data = ApiUtil.send_get_request(url, headers)
        if data and data.get("code") == "200":
            return {
                "daily": data.get("daily", []),
                "updateTime": data.get("updateTime", "")
            }
        return None

    @classmethod
    def upsert_weather_data(cls):
        """更新天气数据（删旧插新）"""
        logger.info("===== 开始处理天气数据 =====")
        now_data = cls.get_weather_now()
        forecast_data = cls.get_3d_forecast()

        if not now_data or not forecast_data or not forecast_data.get("daily"):
            logger.error("缺少实时/预报数据，无法处理天气数据")
            return

        conn = DBUtil.get_connection()
        if not conn:
            return

        try:
            today = datetime.now().strftime("%Y-%m-%d")
            forecast_list = forecast_data["daily"]
            forecast_update_time = forecast_data["updateTime"]

            for forecast in forecast_list:
                fx_date = forecast.get("fxDate", "")
                if not fx_date:
                    logger.warning("预报数据缺少日期字段，跳过")
                    continue

                tempMax = forecast.get("tempMax", "")
                tempMin = forecast.get("tempMin", "")
                iconDay = forecast.get("iconDay", "")
                textDay = forecast.get("textDay", "")
                weekDay = DateUtil.get_weekday(fx_date)

                if fx_date == today:
                    temp = now_data.get("temp", "")
                    feelslike = now_data.get("feelsLike", "")
                    icon = now_data.get("icon", "")
                    text = now_data.get("text", "")
                    windDir = now_data.get("windDir", "")
                    windScale = now_data.get("windScale", "")
                    humidity = now_data.get("humidity", "")
                    obsTime = DateUtil.convert_time_format(now_data.get("obsTime", ""))
                else:
                    temp = ""
                    feelslike = ""
                    icon = ""
                    text = ""
                    windDir = forecast.get("windDirDay", "")
                    windScale = forecast.get("windScaleDay", "")
                    humidity = forecast.get("humidity", "")
                    obsTime = DateUtil.convert_time_format(forecast_update_time)

                updateTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 删除旧数据
                delete_sql = "DELETE FROM weather WHERE date = %s"
                _, del_count = DBUtil.execute_sql(conn, delete_sql, (fx_date,), commit=True)
                logger.info(f"删除 {fx_date} 旧天气数据 {del_count} 条")

                # 插入新数据
                insert_sql = """
                INSERT INTO weather (
                    date, temp, feelslike, icon, textDay, text, windDir, 
                    windScale, humidity, obsTime, updateTime, weekDay, 
                    tempMax, tempMin, iconDay
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                insert_params = (
                    fx_date, temp, feelslike, icon, textDay, text, windDir,
                    windScale, humidity, obsTime, updateTime, weekDay,
                    tempMax, tempMin, iconDay
                )
                _, ins_count = DBUtil.execute_sql(conn, insert_sql, insert_params, commit=True)
                if ins_count > 0:
                    logger.info(f"插入 {fx_date} 天气数据成功（{weekDay}）")

            logger.info("天气数据处理完成")
        finally:
            DBUtil.close_connection(conn)


class HitokotoHandler:
    """一言数据处理模块（完全未动）"""

    @staticmethod
    def get_hitokoto_data():
        """获取一言接口数据"""
        url = API_CONFIG["hitokoto"]["url"]
        data = ApiUtil.send_get_request(url)
        if not data:
            return None

        hitokoto = data.get("hitokoto", "")
        from_content = data.get("from", "")
        if hitokoto and from_content:
            return {"hitokoto": hitokoto, "from": from_content}

        logger.warning("一言接口返回空字段")
        return None

    @classmethod
    def process_hitokoto(cls):
        """处理一言数据主流程"""
        logger.info("===== 开始处理一言数据 =====")
        hitokoto_data = cls.get_hitokoto_data()
        if not hitokoto_data:
            logger.error("获取一言数据失败")
            return

        conn = DBUtil.get_connection()
        if not conn:
            return

        try:
            insert_sql = """
            INSERT INTO hitokoto (hitokoto, `from`)
            VALUES (%(hitokoto)s, %(from)s)
            """
            _, row_count = DBUtil.execute_sql(conn, insert_sql, hitokoto_data, commit=True)
            if row_count > 0:
                logger.info(f"成功插入一言数据：{hitokoto_data['hitokoto']}（来源：{hitokoto_data['from']}）")
        finally:
            DBUtil.close_connection(conn)


# ===================== 主程序入口 =====================
def main():
    """主执行函数（完全未动）"""
    logger.info("===== 程序开始执行 =====")

    try:
        CalendarHandler.process_calendar()
    except Exception as e:
        logger.error(f"日历模块执行异常: {e}，继续执行其他模块")

    try:
        WeatherHandler.upsert_weather_data()
    except Exception as e:
        logger.error(f"天气模块执行异常: {e}，继续执行其他模块")

    try:
        HitokotoHandler.process_hitokoto()
    except Exception as e:
        logger.error(f"一言模块执行异常: {e}")

    logger.info("===== 程序执行完成 =====")


if __name__ == "__main__":
    main()
