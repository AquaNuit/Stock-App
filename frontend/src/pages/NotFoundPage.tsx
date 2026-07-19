import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { Page } from '@/components/ui/Page'
import { Button } from '@/components/ui/Button'

export default function NotFoundPage() {
  return (
    <Page title="Page not found">
      <div className="notfound">
        <Compass size={40} />
        <h2>404 — Lost in the markets</h2>
        <p className="muted">The page you’re looking for doesn’t exist.</p>
        <Link to="/">
          <Button variant="primary">Back to Dashboard</Button>
        </Link>
      </div>
    </Page>
  )
}
