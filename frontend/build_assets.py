import os
import json
import glob
from PIL import Image

# Directories
BASE_DIR = r"d:\por\COMPITITOR\frontend\public\assets"
FURNITURE_DIR = os.path.join(BASE_DIR, "furniture")
CHARACTERS_DIR = os.path.join(BASE_DIR, "characters")
FLOORS_DIR = os.path.join(BASE_DIR, "floors")
WALLS_DIR = os.path.join(BASE_DIR, "walls")

def rgb_to_hex(r, g, b, a):
    if a == 0:
        return ""
    return f"#{r:02X}{g:02X}{b:02X}"

def decode_image_to_sprite_data(image_path, crop_box=None):
    """Decodes PNG pixels into a 2D array of hex colors."""
    img = Image.open(image_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    if crop_box:
        img = img.crop(crop_box)
        
    width, height = img.size
    pixels = img.load()
    
    sprite_data = []
    for y in range(height):
        row = []
        for x in range(width):
            r, g, b, a = pixels[x, y]
            row.append(rgb_to_hex(r, g, b, a))
        sprite_data.append(row)
    return sprite_data

def build_furniture():
    print("Building furniture...")
    catalog = []
    sprites = {}
    
    # Traverse all directories in furniture_dir
    for folder in os.listdir(FURNITURE_DIR):
        folder_path = os.path.join(FURNITURE_DIR, folder)
        if not os.path.isdir(folder_path):
            continue
            
        manifest_path = os.path.join(folder_path, "manifest.json")
        if not os.path.exists(manifest_path):
            continue
            
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            
        # Context base fields from manifest
        base_context = {
            "groupId": manifest["id"],
            "category": manifest["category"],
            "canPlaceOnWalls": manifest.get("canPlaceOnWalls", False),
            "canPlaceOnSurfaces": manifest.get("canPlaceOnSurfaces", False),
            "backgroundTiles": manifest.get("backgroundTiles", 0),
            "rotationScheme": manifest.get("rotationScheme"),
            "isDesk": manifest["category"] == "desks"
        }
        
        def walk(node, context):
            if node["type"] == "asset":
                asset_id = node["id"]
                file_name = node.get("file", f"{asset_id}.png")
                file_path = os.path.join(folder_path, file_name)
                
                if not os.path.exists(file_path):
                    # Fallback check
                    file_path = os.path.join(folder_path, f"{manifest['id']}.png")
                    
                if not os.path.exists(file_path):
                    print(f"Warning: PNG not found for {asset_id} at {file_path}")
                    return
                
                # Build label
                label = manifest["name"]
                orientation = node.get("orientation") or context.get("orientation")
                state = node.get("state") or context.get("state")
                frame = node.get("frame")
                
                if orientation:
                    label += f" - {orientation.capitalize()}"
                if state:
                    label += f" - {state.capitalize()}"
                if frame is not None:
                    label += f" - Frame {frame + 1}"
                    
                entry = {
                    "id": asset_id,
                    "label": label,
                    "category": context["category"],
                    "width": node["width"],
                    "height": node["height"],
                    "footprintW": node["footprintW"],
                    "footprintH": node["footprintH"],
                    "isDesk": context["isDesk"],
                    "canPlaceOnWalls": context["canPlaceOnWalls"],
                    "canPlaceOnSurfaces": context["canPlaceOnSurfaces"],
                    "backgroundTiles": context["backgroundTiles"]
                }
                
                if context.get("groupId"):
                    entry["groupId"] = context["groupId"]
                if orientation:
                    entry["orientation"] = orientation
                if state:
                    entry["state"] = state
                if context.get("mirrorSide") or node.get("mirrorSide"):
                    entry["mirrorSide"] = True
                if context.get("rotationScheme"):
                    entry["rotationScheme"] = context["rotationScheme"]
                if context.get("animationGroup"):
                    entry["animationGroup"] = context["animationGroup"]
                if frame is not None:
                    entry["frame"] = frame
                    
                catalog.append(entry)
                
                # Decode PNG
                sprites[asset_id] = decode_image_to_sprite_data(file_path)
                
            elif node["type"] == "group":
                new_context = context.copy()
                
                if node.get("groupType") == "animation":
                    # Create animationGroup ID
                    state_suffix = f"_{context.get('state')}" if context.get('state') else ""
                    new_context["animationGroup"] = f"{context['groupId']}_{context.get('orientation', '')}{state_suffix}"
                    
                if "orientation" in node:
                    new_context["orientation"] = node["orientation"]
                if "state" in node:
                    new_context["state"] = node["state"]
                if "mirrorSide" in node:
                    new_context["mirrorSide"] = node["mirrorSide"]
                    
                for member in node["members"]:
                    walk(member, new_context)
        
        # Traverse manifest
        if manifest["type"] == "asset":
            # Simple single asset
            walk(manifest, base_context)
        else:
            # Group root
            for member in manifest["members"]:
                walk(member, base_context)
                
    output_path = os.path.join(BASE_DIR, "furniture-catalog.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"catalog": catalog, "sprites": sprites}, f, indent=2)
    print(f"Wrote furniture catalog containing {len(catalog)} assets and sprites to {output_path}")

def build_characters():
    print("Building characters...")
    characters_data = []
    
    for i in range(6):
        file_path = os.path.join(CHARACTERS_DIR, f"char_{i}.png")
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found")
            continue
            
        # char_X.png is 112x96 (7 cols x 3 rows of 16x32 frames)
        # Row 0: down
        # Row 1: up
        # Row 2: right
        
        down_frames = []
        up_frames = []
        right_frames = []
        
        for r in range(3):
            for c in range(7):
                box = (c * 16, r * 32, (c + 1) * 16, (r + 1) * 32)
                sprite = decode_image_to_sprite_data(file_path, box)
                
                if r == 0:
                    down_frames.append(sprite)
                elif r == 1:
                    up_frames.append(sprite)
                else:
                    right_frames.append(sprite)
                    
        characters_data.append({
            "down": down_frames,
            "up": up_frames,
            "right": right_frames
        })
        
    output_path = os.path.join(BASE_DIR, "characters.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(characters_data, f)
    print(f"Wrote characters data to {output_path}")

def build_floors():
    print("Building floors...")
    floors_data = []
    
    # Read floor_0.png to floor_8.png (9 patterns)
    for i in range(9):
        file_path = os.path.join(FLOORS_DIR, f"floor_{i}.png")
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found")
            continue
            
        sprite = decode_image_to_sprite_data(file_path)
        floors_data.append(sprite)
        
    output_path = os.path.join(BASE_DIR, "floors.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(floors_data, f)
    print(f"Wrote floors data to {output_path}")

def build_walls():
    print("Building walls...")
    # Read wall_0.png (64x128 -> 4 columns x 4 rows of 16x32 sprites = 16 sprites)
    file_path = os.path.join(WALLS_DIR, "wall_0.png")
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return
        
    sprites = []
    for r in range(4):
        for c in range(4):
            box = (c * 16, r * 32, (c + 1) * 16, (r + 1) * 32)
            sprite = decode_image_to_sprite_data(file_path, box)
            sprites.append(sprite)
            
    # wallSets format: SpriteData[][] (array of wall sets, where each set is an array of 16 sprites)
    walls_data = [sprites]
    
    output_path = os.path.join(BASE_DIR, "walls.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(walls_data, f)
    print(f"Wrote walls data to {output_path}")

if __name__ == "__main__":
    build_furniture()
    build_characters()
    build_floors()
    build_walls()
    print("All assets processed successfully!")
