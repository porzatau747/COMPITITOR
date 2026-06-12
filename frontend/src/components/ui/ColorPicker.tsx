import type { ColorValue } from './types.js';

interface ColorPickerProps {
  value: ColorValue;
  onChange: ((color: ColorValue) => void) | ((color: ColorValue | null) => void);
  colorize?: boolean;
  showColorizeToggle?: boolean;
}

export function ColorPicker(props: ColorPickerProps) {
  void props;
  return null;
}
