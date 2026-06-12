interface ItemSelectProps {
  width: number;
  height: number;
  selected: boolean;
  onClick: () => void;
  title: string;
  deps: unknown[];
  draw: (ctx: CanvasRenderingContext2D, width: number, height: number) => void;
}

export function ItemSelect(props: ItemSelectProps) {
  void props;
  return null;
}
