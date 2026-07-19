import { motion } from 'framer-motion'
import type { ReactNode } from 'react'

// Page-level entrance animation (fade + slight rise).
export function Page({ children, title, actions }: { children: ReactNode; title?: ReactNode; actions?: ReactNode }) {
  return (
    <motion.div
      className="page"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      {(title || actions) && (
        <div className="page__head">
          <h1 className="page__title">{title}</h1>
          {actions && <div className="page__actions">{actions}</div>}
        </div>
      )}
      {children}
    </motion.div>
  )
}

// Stagger container used for grids of cards.
export function Stagger({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div
      className={className}
      initial="hidden"
      animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06 } } }}
    >
      {children}
    </motion.div>
  )
}

export function StaggerItem({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div
      className={className}
      variants={{
        hidden: { opacity: 0, y: 14 },
        show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] } },
      }}
    >
      {children}
    </motion.div>
  )
}
