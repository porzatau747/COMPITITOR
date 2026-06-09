def adapt_for_advice(analysis: dict) -> dict:
    # If the AI model has dynamically generated the local adaptation, return it directly.
    target_keys = ["local_angle", "suggested_hook", "caption_draft", "creative_direction", "sales_bridge", "cta"]
    if all(k in analysis for k in target_keys):
        return {k: analysis[k] for k in target_keys}
        
    # Fallback to static mock templates if the AI did not generate them (e.g. in Mock mode)
    cats=analysis.get("detected_product_category") or ["IT"]
    cat=" / ".join(cats)
    hook=analysis.get("hook") or "ไม่แน่ใจว่าสเปกพอไหม?"
    return {
      "local_angle": f"หยิบ pain point เรื่อง {cat} มาเล่าแบบร้านไอทีท้องถิ่น ให้ลูกค้าสามร้อยยอดส่งงบหรืออาการมาให้ช่วยดู",
      "suggested_hook": hook if len(hook) <= 90 else hook[:87] + "...",
      "caption_draft": f"{hook}\nไม่แน่ใจว่าสเปกพอไหม หรือควรซ่อม/อัปเกรดก่อนซื้อใหม่ ทักเพจให้แอดมิน Advice สามร้อยยอดช่วยดูได้ครับ",
      "creative_direction": "ทำภาพเช็กลิสต์ 3–5 ข้อ หรือถ่ายของจริงในร้านพร้อมป้ายคำถามสั้น ๆ",
      "sales_bridge": "ไม่แน่ใจว่าสเปกพอไหม ส่งรุ่น/งบ/อาการมาให้แอดมินช่วยดูได้",
      "cta": "ทักเพจ Advice สามร้อยยอดได้เลย มีบริการ รับ-ส่ง สินค้าและเครื่องซ่อม"
    }
