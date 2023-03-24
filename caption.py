from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap

def caption_image(image_file, caption, font="impact.ttf"):
    img = Image.open(image_file)
    draw = ImageDraw.Draw(img)

    font_size = int(img.width/16)
    font = ImageFont.truetype("impact.ttf", font_size)

    caption = textwrap.fill(text=caption, width=img.width/(font_size/2))

    caption_w, caption_h = draw.textsize(caption, font=font)
    
    draw.text(((img.width-caption_w)/2, (img.height-caption_h)/8), # position
              caption, # text
              (255,255,255), # color
              font=font, # font
              stroke_width=2, # text outline width
              stroke_fill=(0,0,0)) # text outline color

    with BytesIO() as img_bytes:
        img.save(img_bytes, format=img.format)
        content = img_bytes.getvalue()
    
    return content

