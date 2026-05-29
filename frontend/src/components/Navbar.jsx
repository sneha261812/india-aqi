import { NavLink } from 'react-router-dom'
import { Wind, Activity, MessageCircle, Cpu, MapPin, BarChart2 } from 'lucide-react'

const LINKS = [
  { to: '/',        icon: MapPin,          label: 'Map'      },
  { to: '/health',  icon: Activity,        label: 'Health'   },
  { to: '/chat',    icon: MessageCircle,   label: 'AI Chat'  },
  { to: '/devices', icon: Cpu,             label: 'Devices'  },
  { to: '/states',  icon: BarChart2,       label: 'States'   },
]

export default function Navbar() {
  return (
    <nav
      className="sticky top-0 z-50 border-b"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        {/* Logo */}
        <NavLink to="/" className="flex items-center gap-2">
          <Wind className="h-6 w-6 text-orange-500" />
          <span className="font-display text-lg font-bold tracking-tight">
            India <span className="text-orange-500">AQI</span>
          </span>
        </NavLink>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {LINKS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition ` +
                (isActive
                  ? 'bg-orange-500/10 text-orange-400'
                  : 'text-gray-400 hover:text-white')
              }
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{label}</span>
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
