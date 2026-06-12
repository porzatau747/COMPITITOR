interface ItemSelectProps {
  value?: string | number;
  onChange?: (value: string) => void;
  items?: unknown[];
  width?: number;
  height?: number;
  selected?: boolean;
  onClick?: () => void;
  title?: string;
  deps?: unknown[];
  draw?: (ctx: CanvasRenderingContext2D, width: number, height: number) => void;
}

export function ItemSelect(props: ItemSelectProps) {
  return <button type="button" hidden title={props.title} onClick={props.onClick} data-selected={props.selected} />;
}
