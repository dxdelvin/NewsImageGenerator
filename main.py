import streamlit as st
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import tempfile


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def create_news_image(background_url, tag_text, title_text, logo_url):
    try:
        response = requests.get(background_url)
        background = Image.open(BytesIO(response.content)).convert("RGB")

        min_side = min(background.size)
        left = (background.width - min_side) // 2
        top = (background.height - min_side) // 2
        background = background.crop((left, top, left + min_side, top + min_side))
        background = background.resize((1080, 1080))

        response = requests.get(logo_url)
        logo = Image.open(BytesIO(response.content)).convert("RGBA")
        logo = logo.resize((100, 100))

        draw = ImageDraw.Draw(background)

        # Try to use font files if available, otherwise use default fonts
        try:
            font_tag = ImageFont.truetype("arialbd.ttf", 48)
            font_title = ImageFont.truetype("arialbd.ttf", 55)
            font_story = ImageFont.truetype("arial.ttf", 34)
        except IOError:
            # Fallback to default font
            font_tag = ImageFont.load_default()
            font_title = ImageFont.load_default()
            font_story = ImageFont.load_default()

        margin_top = 50
        margin_right = 50
        margin_left = 50
        margin_bottom = 50
        spacing = 20

        read_more_text = "Read the in-depth story on\ndailyequity.in"
        read_more_padding = 20
        try:
            read_more_bbox = draw.multiline_textbbox((0, 0), read_more_text, font=font_story)
        except AttributeError:
            read_more_bbox = draw.textbbox((0, 0), read_more_text, font=font_story)
        text_width = read_more_bbox[2] - read_more_bbox[0]
        text_height = read_more_bbox[3] - read_more_bbox[1]

        read_more_w = text_width + 2 * read_more_padding
        read_more_h = text_height + 2 * read_more_padding

        total_read_more_width = read_more_w + spacing + logo.width

        read_more_x = 1080 - margin_right - total_read_more_width
        read_more_y = margin_top

        read_more_bg = Image.new("RGBA", (read_more_w, read_more_h), (0, 0, 0, 150))
        background.paste(read_more_bg, (read_more_x, read_more_y), read_more_bg)

        draw.multiline_text(
            (read_more_x + read_more_padding, read_more_y + read_more_padding),
            read_more_text,
            font=font_story,
            fill=(255, 255, 255)
        )

        logo_x = read_more_x + read_more_w + spacing
        logo_y = read_more_y + (read_more_h - logo.height) // 2
        background.paste(logo, (logo_x, logo_y), logo)

        tag_padding = 20
        tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
        tag_text_width = tag_bbox[2] - tag_bbox[0]
        tag_text_height = tag_bbox[3] - tag_bbox[1]
        tag_w = tag_text_width + 2 * tag_padding
        tag_h = tag_text_height + 2 * tag_padding
        tag_radius = tag_h // 2

        tag_x = margin_left

        title_text = " ".join(title_text.splitlines())
        title_padding = 30
        max_title_bg_width = 1080 - margin_left - margin_right
        available_wrap_width = max_title_bg_width - 2 * title_padding

        title_lines = wrap_text(title_text, font_title, available_wrap_width, draw)

        line_heights = []
        max_line_width = 0
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            line_heights.append(line_height)
            if line_width > max_line_width:
                max_line_width = line_width
        line_spacing = 10
        total_title_text_height = sum(line_heights) + line_spacing * (len(title_lines) - 1)

        title_bg_w = max_line_width + 2 * title_padding
        title_bg_h = total_title_text_height + 2 * title_padding

        total_bottom_height = tag_h + spacing + title_bg_h
        start_y = 1080 - margin_bottom - total_bottom_height

        tag_y = start_y
        title_x = margin_left
        title_y = tag_y + tag_h + spacing

        tag_bg = Image.new("RGBA", (tag_w, tag_h), (255, 165, 0, 255))
        draw_tag = ImageDraw.Draw(tag_bg)
        draw_tag.rounded_rectangle((0, 0, tag_w, tag_h), radius=tag_radius, fill=(255, 165, 0))
        background.paste(tag_bg, (tag_x, tag_y), tag_bg)

        tag_text_x = tag_x + (tag_w - tag_text_width) // 2
        tag_text_y = tag_y + (tag_h - tag_text_height) // 2
        draw.text((tag_text_x, tag_text_y), tag_text, font=font_tag, fill=(0, 0, 0))

        title_bg = Image.new("RGBA", (title_bg_w, title_bg_h), (0, 0, 0, 180))
        title_bg = title_bg.filter(ImageFilter.GaussianBlur(10))
        background.paste(title_bg, (title_x, title_y), title_bg)

        current_y = title_y + title_padding
        for line, line_height in zip(title_lines, line_heights):
            bbox = draw.textbbox((0, 0), line, font=font_title)
            line_width = bbox[2] - bbox[0]
            # Center the line inside the title background.
            line_x = title_x + title_padding + (max_line_width - line_width) // 2
            draw.text((line_x, current_y), line, font=font_title, fill=(255, 255, 255))
            current_y += line_height + line_spacing

        return background
    except Exception as e:
        st.error(f"Error creating image: {str(e)}")
        return None


# Streamlit app
st.title("News Image Generator")
st.write("By dxdelvin")

# Input fields
with st.form("image_generator_form"):
    col1, col2 = st.columns(2)

    with col1:
             tag_text = st.text_input("Tag Text", value="GLOBAL MARKETS")

    with col2:
              website_name = st.text_input("Website Name", value="dailyequity.in")

    title_text = st.text_area("Title Text",
                              value="India Cuts Rates For First Time In Nearly Five Years; Indians To Enjoy 25 bps Cut")

    # Option to upload images instead of using URLs
    st.write("Upload images:")
    col3, col4 = st.columns(2)

    with col3:
        background_file = st.file_uploader("Upload Background Image", type=["jpg", "jpeg", "png"])

    with col4:
        logo_file = st.file_uploader("Upload Logo", type=["jpg", "jpeg", "png"])

    # Customization options
    st.write("Customization Options:")
    col5, col6 = st.columns(2)

    with col5:
        tag_color = st.color_picker("Tag Color", value="#FFA500")  # Orange

    with col6:
        title_bg_opacity = st.slider("Title Background Opacity", 0, 255, 180)

    submitted = st.form_submit_button("Generate Image")

if submitted:
    # Process uploaded files if provided
    if background_file is not None:
        background_data = background_file.getvalue()
        background_url = "uploaded_background"

    if logo_file is not None:
        logo_data = logo_file.getvalue()
        logo_url = "uploaded_logo"

    # Show spinner while processing
    with st.spinner("Generating news image..."):
        if background_url == "uploaded_background" or logo_url == "uploaded_logo":
            # Create a temporary function to handle uploaded files
            def create_news_image_with_uploads():
                try:
                    # Handle background image
                    if background_url == "uploaded_background":
                        background = Image.open(BytesIO(background_data)).convert("RGB")
                    else:
                        response = requests.get(background_url)
                        background = Image.open(BytesIO(response.content)).convert("RGB")

                    min_side = min(background.size)
                    left = (background.width - min_side) // 2
                    top = (background.height - min_side) // 2
                    background = background.crop((left, top, left + min_side, top + min_side))
                    background = background.resize((1080, 1080))

                    # Handle logo
                    if logo_url == "uploaded_logo":
                        logo = Image.open(BytesIO(logo_data)).convert("RGBA")
                    else:
                        response = requests.get(logo_url)
                        logo = Image.open(BytesIO(response.content)).convert("RGBA")

                    logo = logo.resize((100, 100))

                    # Rest of the image creation code (same as before)
                    draw = ImageDraw.Draw(background)

                    try:
                        font_tag = ImageFont.truetype("arialbd.ttf", 48)
                        font_title = ImageFont.truetype("arialbd.ttf", 55)
                        font_story = ImageFont.truetype("arial.ttf", 34)
                    except IOError:
                        font_tag = ImageFont.load_default()
                        font_title = ImageFont.load_default()
                        font_story = ImageFont.load_default()

                    margin_top = 50
                    margin_right = 50
                    margin_left = 50
                    margin_bottom = 50
                    spacing = 20

                    read_more_text = f"Read the in-depth story on\n{website_name}"
                    read_more_padding = 20
                    try:
                        read_more_bbox = draw.multiline_textbbox((0, 0), read_more_text, font=font_story)
                    except AttributeError:
                        read_more_bbox = draw.textbbox((0, 0), read_more_text, font=font_story)
                    text_width = read_more_bbox[2] - read_more_bbox[0]
                    text_height = read_more_bbox[3] - read_more_bbox[1]

                    read_more_w = text_width + 2 * read_more_padding
                    read_more_h = text_height + 2 * read_more_padding

                    total_read_more_width = read_more_w + spacing + logo.width

                    read_more_x = 1080 - margin_right - total_read_more_width
                    read_more_y = margin_top

                    read_more_bg = Image.new("RGBA", (read_more_w, read_more_h), (0, 0, 0, 150))
                    background.paste(read_more_bg, (read_more_x, read_more_y), read_more_bg)

                    draw.multiline_text(
                        (read_more_x + read_more_padding, read_more_y + read_more_padding),
                        read_more_text,
                        font=font_story,
                        fill=(255, 255, 255)
                    )

                    logo_x = read_more_x + read_more_w + spacing
                    logo_y = read_more_y + (read_more_h - logo.height) // 2
                    background.paste(logo, (logo_x, logo_y), logo)

                    tag_padding = 20
                    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
                    tag_text_width = tag_bbox[2] - tag_bbox[0]
                    tag_text_height = tag_bbox[3] - tag_bbox[1]
                    tag_w = tag_text_width + 2 * tag_padding
                    tag_h = tag_text_height + 2 * tag_padding
                    tag_radius = tag_h // 2

                    tag_x = margin_left

                    title_text_clean = " ".join(title_text.splitlines())
                    title_padding = 30
                    max_title_bg_width = 1080 - margin_left - margin_right
                    available_wrap_width = max_title_bg_width - 2 * title_padding

                    title_lines = wrap_text(title_text_clean, font_title, available_wrap_width, draw)

                    line_heights = []
                    max_line_width = 0
                    for line in title_lines:
                        bbox = draw.textbbox((0, 0), line, font=font_title)
                        line_width = bbox[2] - bbox[0]
                        line_height = bbox[3] - bbox[1]
                        line_heights.append(line_height)
                        if line_width > max_line_width:
                            max_line_width = line_width
                    line_spacing = 10
                    total_title_text_height = sum(line_heights) + line_spacing * (len(title_lines) - 1)

                    title_bg_w = max_line_width + 2 * title_padding
                    title_bg_h = total_title_text_height + 2 * title_padding

                    total_bottom_height = tag_h + spacing + title_bg_h
                    start_y = 1080 - margin_bottom - total_bottom_height

                    tag_y = start_y
                    title_x = margin_left
                    title_y = tag_y + tag_h + spacing

                    # Convert color picker string to RGB tuple
                    hex_color = tag_color.lstrip('#')
                    tag_rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
                    tag_rgba = tag_rgb + (255,)

                    tag_bg = Image.new("RGBA", (tag_w, tag_h), tag_rgba)
                    draw_tag = ImageDraw.Draw(tag_bg)
                    draw_tag.rounded_rectangle((0, 0, tag_w, tag_h), radius=tag_radius, fill=tag_rgba)
                    background.paste(tag_bg, (tag_x, tag_y), tag_bg)

                    tag_text_x = tag_x + (tag_w - tag_text_width) // 2
                    tag_text_y = tag_y + (tag_h - tag_text_height) // 2
                    draw.text((tag_text_x, tag_text_y), tag_text, font=font_tag, fill=(0, 0, 0))

                    title_bg = Image.new("RGBA", (title_bg_w, title_bg_h), (0, 0, 0, title_bg_opacity))
                    title_bg = title_bg.filter(ImageFilter.GaussianBlur(10))
                    background.paste(title_bg, (title_x, title_y), title_bg)

                    current_y = title_y + title_padding
                    for line, line_height in zip(title_lines, line_heights):
                        bbox = draw.textbbox((0, 0), line, font=font_title)
                        line_width = bbox[2] - bbox[0]
                        # Center the line inside the title background.
                        line_x = title_x + title_padding + (max_line_width - line_width) // 2
                        draw.text((line_x, current_y), line, font=font_title, fill=(255, 255, 255))
                        current_y += line_height + line_spacing

                    return background

                except Exception as e:
                    st.error(f"Error creating image: {str(e)}")
                    return None


            result_image = create_news_image_with_uploads()
        else:
            result_image = create_news_image(background_url, tag_text, title_text, logo_url)

        if result_image:
            # Display the generated image
            st.success("Image generated successfully!")
            st.image(result_image, caption="Generated News Image", use_column_width=True)

            # Convert image to bytes for download
            img_byte_arr = BytesIO()
            result_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Provide download button directly with the bytes
            st.download_button(
                label="Download Image",
                data=img_byte_arr,
                file_name="news_image.png",
                mime="image/png"
            )

