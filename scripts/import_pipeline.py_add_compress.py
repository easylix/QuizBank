def _compress_image_data(img_data: bytes, target_b64_kb: int = 40) -> bytes:
    """Compress image so base64 <= target_b64_kb KB"""
    try:
        from PIL import Image
        import io
    except ImportError:
        return img_data

    b64 = base64.b64encode(img_data).decode()
    if len(b64) / 1024 <= target_b64_kb:
        return img_data

    try:
        img = Image.open(io.BytesIO(img_data))
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        scale = 0.85
        while True:
            w, h = img.size
            nw, nh = int(w * scale), int(h * scale)
            if nw < 30 or nh < 30:
                break
            resized = img.resize((nw, nh), Image.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format='PNG', optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode()
            if len(b64) / 1024 <= target_b64_kb:
                return buf.getvalue()
            scale *= 0.8
    except Exception:
        pass
    return img_data
