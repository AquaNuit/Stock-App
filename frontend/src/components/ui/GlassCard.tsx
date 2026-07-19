import clsx from 'clsx'
import type { CSSProperties, ReactNode } from 'react'

interface GlassCardProps {
  children: ReactNode
  className?: string
  title?: ReactNode
  subtitle?: ReactNode
  actions?: ReactNode
  padded?: boolean
  style?: CSSProperties
  hover?: boolean
  as?: 'div' | 'section' | 'article'
}

export function GlassCard({
  children,
  className,
  title,
  subtitle,
  actions,
  padded = true,
  style,
  hover = false,
  as = 'div',
}: GlassCardProps) {
  const Tag = as
  return (
    <Tag className={clsx('glass-card', hover && 'glass-card--hover', className)} style={style}>
      {(title || actions) && (
        <header className="glass-card__head">
          <div>
            {title && <h3 className="glass-card__title">{title}</h3>}
            {subtitle && <p className="glass-card__subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="glass-card__actions">{actions}</div>}
        </header>
      )}
      <div className={padded ? 'glass-card__body' : 'glass-card__body glass-card__body--flush'}>
        {children}
      </div>
    </Tag>
  )
}
