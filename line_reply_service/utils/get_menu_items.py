from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuArea, RichMenuBounds, MessageAction
from config.config import Config
import logging
from PIL import Image, ImageDraw, ImageFont
import requests
import os
from zipfile import ZipFile
from io import BytesIO

logging.basicConfig(filename='error.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)

def download_font(font_dir="fonts"):
    url = "https://noto-website-2.storage.googleapis.com/pkgs/NotoSansTC.zip"

    font_filename = "NotoSansTC-Regular.otf"
    save_path = os.path.join(font_dir, font_filename)

    if os.path.exists(save_path):
        return save_path

    os.makedirs(font_dir, exist_ok=True)
    response = requests.get(url)

    if response.status_code == 200:
        with ZipFile(BytesIO(response.content)) as z:
            print("📂 解壓縮中...")
            for name in z.namelist():
                if name.endswith(font_filename):
                    z.extract(name, path=font_dir)
                    extracted_path = os.path.join(font_dir, name)
                    final_path = os.path.join(font_dir, font_filename)
                    os.rename(extracted_path, final_path)
                    print(f"✅ 字型已儲存：{final_path}")
                    return final_path
            print("❌ 找不到指定字型檔")
    else:
        print("❌ 下載失敗，請確認網址")

    return None

# 使用範例
def generate_rich_menu_background(output_path="with_text.png"):
    font_path = download_font()
    img_width, img_height = 2500, 843
    img = Image.new('RGB', (img_width, img_height), color=(0, 0, 0))  # 黑底
    draw = ImageDraw.Draw(img)

    font_size = 150
    font = ImageFont.truetype(font_path, font_size)

    left_color = (0, 50, 0)        # 深綠色
    right_color = (0, 0, 0)          # 黑色
    draw.rectangle([0, 0, img_width // 2, img_height], fill=left_color)
    draw.rectangle([img_width // 2, 0, img_width, img_height], fill=right_color)


    # 畫分隔線（中間線）
    line_x = img_width // 2
    draw.line([(line_x, 0), (line_x, img_height)], fill=(255, 255, 255), width=5)

    # 畫左邊文字（白色）
    left_text = "我要上傳照片"
    left_text_size = draw.textbbox((0, 0), left_text, font=font)
    left_text_width = left_text_size[2] - left_text_size[0]
    left_text_height = left_text_size[3] - left_text_size[1]
    left_x = (img_width // 2 - left_text_width) // 2
    left_y = (img_height - left_text_height) // 2
    draw.text((left_x, left_y), left_text, font=font, fill=(255, 255, 255))
    # 畫右邊文字（白色）
    right_text = "使用自訂參數"
    right_text_size = draw.textbbox((0, 0), right_text, font=font)
    right_text_width = right_text_size[2] - right_text_size[0]
    right_text_height = right_text_size[3] - right_text_size[1]
    right_x = img_width // 2 + (img_width // 2 - right_text_width) // 2
    right_y = (img_height - right_text_height) // 2
    draw.text((right_x, right_y), right_text, font=font, fill=(255, 255, 255))

    img.save(output_path)
    print(f"✅ 圖片已儲存：{output_path}")

def resize_and_compress_image(input_path, output_path, size=(2500, 843)):
    """
    將圖片調整成符合 LINE Rich Menu 規格並壓縮儲存
    """
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        resized_img = img.resize(size)
        resized_img.save(output_path, format="PNG", optimize=True)
    logging.info(f"已調整圖片尺寸並儲存：{output_path}")

def create_rich_menu():
    try:
        logging.info("🔧 開始產生 Rich Menu 背景圖...")
        # Step 1: 在原圖上加文字
        font_path = download_font()
        if not font_path:
            print("❌ 無法載入字型，請確認下載是否成功")
            raise Exception("字型載入失敗")
        generate_rich_menu_background()

        logging.info("🔧 開始調整圖片大小...")
        # Step 2: 調整尺寸
        resize_and_compress_image("with_text.png", "rich_menu.png", size=(2500, 843))

        logging.info("開始建立 Rich Menu...")
        # Step 3: 建立 Rich Menu
        rich_menu = RichMenu(
            size={"width": 2500, "height": 843},
            selected=False,
            name="主選單",
            chat_bar_text="點我展開選單",
            areas=[
                RichMenuArea(
                    bounds=RichMenuBounds(x=0, y=0, width=1250, height=843),
                    action=MessageAction(label="左邊", text="我要上傳照片")
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(x=1250, y=0, width=1250, height=843),
                    action=MessageAction(label="右邊", text="使用自訂參數")
                )
            ]
        )

        rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu)
        logging.info(f"✅ RichMenu 建立成功，ID：{rich_menu_id}")

        # Step 4: 上傳圖片
        with open("rich_menu.png", "rb") as f:
            line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", f)
        logging.info("✅ RichMenu 圖片上傳成功")

        # Step 5: 設為預設 Rich Menu
        line_bot_api.set_default_rich_menu(rich_menu_id)
        logging.info("✅ 已設定為預設 Rich Menu")

        print("✅ 圖文選單設定完成！")

    except Exception as e:
        logging.error(f"❌ 圖文選單建立失敗: {e}")
        print(f"發生錯誤：{e}")