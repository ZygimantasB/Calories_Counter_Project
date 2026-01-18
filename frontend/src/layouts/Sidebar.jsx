import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Utensils,
  Scale,
  Dumbbell,
  Activity,
  BarChart3,
  Ruler,
  Trophy,
  Settings,
  ChevronLeft,
  ChevronRight,
  Home,
} from 'lucide-react';
import { useState } from 'react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Food Tracker', href: '/food', icon: Utensils },
  { name: 'Weight Tracker', href: '/weight', icon: Scale },
  { name: 'Workout Tracker', href: '/workout', icon: Dumbbell },
  { name: 'Running Tracker', href: '/running', icon: Activity },
  { name: 'Body Measurements', href: '/body-measurements', icon: Ruler },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Top Foods', href: '/top-foods', icon: Trophy },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-gray-900 border-r border-gray-800 transition-all duration-300 z-40 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg text-gray-100">Health Tracker</span>
          </div>
        )}
        {collapsed && (
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center mx-auto">
            <Activity className="w-5 h-5 text-white" />
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={`p-1.5 rounded-lg hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors ${
            collapsed ? 'absolute -right-3 top-6 bg-gray-900 border border-gray-700 shadow-lg' : ''
          }`}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="p-3 space-y-1 overflow-y-auto h-[calc(100vh-8rem)]">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                isActive
                  ? 'bg-primary-500/20 text-primary-400 font-medium'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              } ${collapsed ? 'justify-center' : ''}`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon
                  className={`w-5 h-5 flex-shrink-0 ${
                    isActive ? 'text-primary-400' : 'text-gray-500 group-hover:text-gray-300'
                  }`}
                />
                {!collapsed && <span>{item.name}</span>}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer - Back to Django */}
      <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-gray-800">
        <a
          href="/"
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-gray-400 hover:bg-gray-800 hover:text-gray-200 ${
            collapsed ? 'justify-center' : ''
          }`}
        >
          <Home className="w-5 h-5 text-gray-500" />
          {!collapsed && <span>Back to Classic View</span>}
        </a>
      </div>
    </aside>
  );
}
