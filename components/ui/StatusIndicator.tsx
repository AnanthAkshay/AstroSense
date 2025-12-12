interface StatusIndicatorProps {
  status: 'low' | 'moderate' | 'high' | 'critical'
  label: string
  value?: string | number
}

export default function StatusIndicator({ status, label, value }: StatusIndicatorProps) {
  const getStatusStyles = (status: string) => {
    switch (status) {
      case 'low':
        return 'bg-green-900/50 text-green-300 border-green-500/30'
      case 'moderate':
        return 'bg-yellow-900/50 text-yellow-300 border-yellow-500/30'
      case 'high':
        return 'bg-orange-900/50 text-orange-300 border-orange-500/30'
      case 'critical':
        return 'bg-red-900/50 text-red-300 border-red-500/30'
      default:
        return 'bg-gray-900/50 text-gray-300 border-gray-500/30'
    }
  }

  return (
    <div className={`
      px-3 py-2 rounded-lg border text-sm font-medium transition-all duration-200
      ${getStatusStyles(status)}
    `}>
      <div className="flex items-center justify-between">
        <span>{label}</span>
        {value && <span className="ml-2 font-mono">{value}</span>}
      </div>
    </div>
  )
}