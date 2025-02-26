import streamlit as st
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def wrap_text(text, font, max_width, draw):
    words, lines, current = text.split(), [], ""
    for word in words:
        test_line = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test_line
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def create_news_image(background, logo, tag_text, title_text, website_name, tag_color, title_bg_opacity):
    try:
        # Process background image: crop to square & resize
        background = background.convert("RGB")
        min_side = min(background.size)
        left = (background.width - min_side) // 2
        top = (background.height - min_side) // 2
        background = background.crop((left, top, left + min_side, top + min_side))
        background = background.resize((1080, 1080), Image.LANCZOS)

        # Process logo
        logo = logo.convert("RGBA").resize((100, 100))
        draw = ImageDraw.Draw(background)

        # Fonts (fallback to default if truetype fonts are unavailable)
        try:
            font_tag = ImageFont.truetype("arialbd.ttf", 48)
            font_title = ImageFont.truetype("arialbd.ttf", 55)
            font_story = ImageFont.truetype("arial.ttf", 34)
        except IOError:
            font_tag = font_title = font_story = ImageFont.load_default()

        # Layout margins and spacing
        margin_top, margin_right, margin_left, margin_bottom, spacing = 50, 50, 50, 50, 20

        # "Read more" section at top right
        read_more_text = f"Read the in-depth story on\n{website_name}"
        read_more_padding = 20
        try:
            bbox = draw.multiline_textbbox((0, 0), read_more_text, font=font_story)
        except AttributeError:
            bbox = draw.textbbox((0, 0), read_more_text, font=font_story)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        read_more_w, read_more_h = text_width + 2 * read_more_padding, text_height + 2 * read_more_padding
        total_read_more_width = read_more_w + spacing + logo.width
        read_more_x = 1080 - margin_right - total_read_more_width
        read_more_y = margin_top
        read_more_bg = Image.new("RGBA", (read_more_w, read_more_h), (0, 0, 0, 150))
        background.paste(read_more_bg, (read_more_x, read_more_y), read_more_bg)
        draw.multiline_text((read_more_x + read_more_padding, read_more_y + read_more_padding),
                            read_more_text, font=font_story, fill=(255, 255, 255))
        logo_x = read_more_x + read_more_w + spacing
        logo_y = read_more_y + (read_more_h - logo.height) // 2
        background.paste(logo, (logo_x, logo_y), logo)

        # Tag settings at bottom left
        tag_padding = 20
        tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
        tag_text_width = tag_bbox[2] - tag_bbox[0]
        tag_text_height = tag_bbox[3] - tag_bbox[1]
        tag_w = tag_text_width + 2 * tag_padding
        tag_h = tag_text_height + 2 * tag_padding
        tag_radius = tag_h // 2
        tag_x = margin_left

        # Title text above tag
        title_clean = " ".join(title_text.splitlines())
        title_padding = 30
        max_title_bg_width = 1080 - margin_left - margin_right
        available_wrap_width = max_title_bg_width - 2 * title_padding
        title_lines = wrap_text(title_clean, font_title, available_wrap_width, draw)
        line_heights, max_line_width = [], 0
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
            line_heights.append(lh)
            if lw > max_line_width:
                max_line_width = lw
        line_spacing = 10
        total_title_text_height = sum(line_heights) + line_spacing * (len(title_lines) - 1)
        title_bg_w = max_line_width + 2 * title_padding
        title_bg_h = total_title_text_height + 2 * title_padding

        total_bottom_height = tag_h + spacing + title_bg_h
        start_y = 1080 - margin_bottom - total_bottom_height
        tag_y = start_y
        title_x = margin_left
        title_y = tag_y + tag_h + spacing

        # Draw tag background using tag_color
        hex_color = tag_color.lstrip('#')
        tag_rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        tag_rgba = tag_rgb + (255,)
        tag_bg = Image.new("RGBA", (tag_w, tag_h), tag_rgba)
        ImageDraw.Draw(tag_bg).rounded_rectangle((0, 0, tag_w, tag_h), radius=tag_radius, fill=tag_rgba)
        background.paste(tag_bg, (tag_x, tag_y), tag_bg)
        tag_text_x = tag_x + (tag_w - tag_text_width) // 2
        tag_text_y = tag_y + (tag_h - tag_text_height) // 2
        draw.text((tag_text_x, tag_text_y), tag_text, font=font_tag, fill=(0, 0, 0))

        # Draw title background with Gaussian blur
        title_bg = Image.new("RGBA", (title_bg_w, title_bg_h), (0, 0, 0, title_bg_opacity))
        title_bg = title_bg.filter(ImageFilter.GaussianBlur(10))
        background.paste(title_bg, (title_x, title_y), title_bg)
        current_y = title_y + title_padding
        for i, line in enumerate(title_lines):
            bbox = draw.textbbox((0, 0), line, font=font_title)
            line_x = title_x + title_padding + (max_line_width - (bbox[2] - bbox[0])) // 2
            draw.text((line_x, current_y), line, font=font_title, fill=(255, 255, 255))
            current_y += line_heights[i] + line_spacing
        return background
    except Exception as e:
        st.error(f"Error creating image: {e}")
        return None


st.title("News Image Generator")
st.write("by dxdelvin")

with st.form("image_generator_form"):
    # Only file upload inputs (no URL fields)
    background_file = st.file_uploader("Upload Background Image", type=["jpg", "jpeg", "png"])
    logo_file = st.file_uploader("Upload Logo", type=["jpg", "jpeg", "png"])

    tag_text = st.text_input("Tag Text", value="GLOBAL MARKETS")
    title_text = st.text_area("Title Text",
                              value="India Cuts Rates For First Time In Nearly Five Years; Indians To Enjoy 25 bps Cut")
    website_name = st.text_input("Website Name", value="dailyequity.in")

    st.write("Customization Options:")
    tag_color = st.color_picker("Tag Color", value="#FFA500")
    title_bg_opacity = st.slider("Title Background Opacity", 0, 255, 180)

    submitted = st.form_submit_button("Generate Image")

if submitted and background_file and logo_file:
    background = Image.open(background_file)
    logo = Image.open(logo_file)
    result_image = create_news_image(background, logo, tag_text, title_text, website_name, tag_color, title_bg_opacity)
    if result_image:
        st.success("Image generated successfully!")
        st.image(result_image, caption="Generated News Image", use_container_width=True)
        buf = BytesIO()
        result_image.save(buf, format='PNG')
        st.download_button("Download Image", buf.getvalue(), "news_image.png", "image/png")
