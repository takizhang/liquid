import { Link, Outlet, useLocation } from 'react-router-dom';

export const Layout = () => {
  const location = useLocation();

  return (
    <div className="min-h-screen grid-bg">
      <header className="border-b border-[rgba(0,255,136,0.1)] backdrop-blur-md bg-[rgba(10,10,15,0.8)] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <Link to="/" className="flex items-center gap-3 group">
              <span className="text-3xl group-hover:animate-pulse">💹</span>
              <div>
                <h1 className="text-xl font-bold text-[#00ff88] glow-green tracking-wider">
                  LIQUIDITY MONITOR
                </h1>
                <p className="text-xs text-gray-500 tracking-widest">宏观流动性监控系统</p>
              </div>
            </Link>
            <nav className="flex gap-2">
              <Link
                to="/"
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  location.pathname === '/'
                    ? 'bg-[rgba(0,255,136,0.15)] text-[#00ff88] border border-[rgba(0,255,136,0.3)] shadow-[0_0_15px_rgba(0,255,136,0.2)]'
                    : 'text-gray-400 hover:text-[#00ff88] hover:bg-[rgba(0,255,136,0.05)]'
                }`}
              >
                ◈ 总览
              </Link>
              <Link
                to="/market/us"
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  location.pathname.startsWith('/market/us')
                    ? 'bg-[rgba(0,170,255,0.15)] text-[#00aaff] border border-[rgba(0,170,255,0.3)] shadow-[0_0_15px_rgba(0,170,255,0.2)]'
                    : 'text-gray-400 hover:text-[#00aaff] hover:bg-[rgba(0,170,255,0.05)]'
                }`}
              >
                🇺🇸 美国
              </Link>
              <Link
                to="/market/china"
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  location.pathname.startsWith('/market/china')
                    ? 'bg-[rgba(255,51,102,0.15)] text-[#ff3366] border border-[rgba(255,51,102,0.3)] shadow-[0_0_15px_rgba(255,51,102,0.2)]'
                    : 'text-gray-400 hover:text-[#ff3366] hover:bg-[rgba(255,51,102,0.05)]'
                }`}
              >
                🇨🇳 中国
              </Link>
              <Link
                to="/market/crypto"
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  location.pathname.startsWith('/market/crypto')
                    ? 'bg-[rgba(168,85,247,0.15)] text-[#a855f7] border border-[rgba(168,85,247,0.3)] shadow-[0_0_15px_rgba(168,85,247,0.2)]'
                    : 'text-gray-400 hover:text-[#a855f7] hover:bg-[rgba(168,85,247,0.05)]'
                }`}
              >
                🪙 加密货币
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-[rgba(0,255,136,0.1)] mt-auto bg-[rgba(10,10,15,0.5)]">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center">
          <p className="text-xs text-gray-600 tracking-widest">
            LIQUIDITY MONITOR v2.0 | <span className="text-[#00ff88]">●</span> LIVE
          </p>
        </div>
      </footer>
    </div>
  );
};
