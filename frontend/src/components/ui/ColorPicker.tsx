import type { ColorValue } from './types.js';

interface ColorPickerProps {
  value?: ColorValue;
  onChange?: (value: ColorValue) => void;
  colorize?: boolean;
  showColorizeToggle?: boolean;
}

export function ColorPicker(props: ColorPickerProps) {
  return <span hidden data-colorize={props.colorize} data-toggle={props.showColorizeToggle} />;
}
