// PropertyRow component - key-value display for detail panels

import { colors } from "../theme"

interface PropertyRowProps {
  label: string
  value: string | React.ReactNode
  labelColor?: string
  valueColor?: string
}

export function PropertyRow({
  label,
  value,
  labelColor = colors.blue,
  valueColor = colors.text,
}: PropertyRowProps) {
  return (
    <text>
      <span fg={labelColor}>
        <strong>{label}: </strong>
      </span>
      {typeof value === "string" ? <span fg={valueColor}>{value}</span> : value}
    </text>
  )
}
