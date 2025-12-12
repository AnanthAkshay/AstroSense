import { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  title?: string
  animate?: boolean
}

export default function Card({ children, className = '', title, animate = true }: CardProps) {
  return (
    <div className={`
      bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-6
      ${animate ? 'animate-fade-in' : ''}
      ${className}
    `}>
      {title && (
        <h3 className="text-xl font-semibold text-astro-cyan mb-4">{title}</h3>
      )}
      {children}
    </div>
  )
}