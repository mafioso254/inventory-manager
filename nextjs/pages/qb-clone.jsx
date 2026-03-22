export default function QbClone() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <header className="sticky top-0 z-50 bg-slate-950/95 backdrop-blur border-b border-slate-800 py-4">
          <div className="flex items-center justify-between gap-4">
            <a className="flex items-center gap-2 text-white font-bold text-lg" href="/">
              <span className="block w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
              QB Accountants
            </a>
            <nav className="hidden md:flex gap-4 text-sm text-slate-300">
              <a href="#why" className="hover:text-white">Why us</a>
              <a href="#features" className="hover:text-white">Features</a>
              <a href="#trust" className="hover:text-white">Trust</a>
              <a href="#pricing" className="hover:text-white">Pricing</a>
            </nav>
            <div className="hidden lg:flex items-center gap-3 text-sm text-slate-300">
              <span>Today 2,114+ sales</span>
              <a href="#" className="px-4 py-2 border border-slate-700 rounded-md hover:bg-slate-800">Sign in</a>
              <a href="#" className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-md font-semibold">Sign up</a>
            </div>
          </div>
        </header>

        <section id="why" className="grid gap-10 lg:grid-cols-2 items-center mt-10">
          <div className="space-y-6 animate-fade-up">
            <p className="text-cyan-300 uppercase tracking-widest font-semibold">Built for accountants</p>
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight">Upgrade your firm with smarter tax, compliance, and client workflows</h1>
            <p className="max-w-xl text-slate-300">One platform for advisory, bookkeeping, review, and payroll — built for midsize firms, CPAs, and growing practices.</p>
            <div className="flex flex-wrap gap-3">
              <a href="#" className="px-6 py-3 rounded-lg bg-cyan-500 text-slate-950 font-bold hover:bg-cyan-400">Start free trial</a>
              <a href="#" className="px-6 py-3 rounded-lg border border-slate-700 hover:bg-slate-800">Book a demo</a>
            </div>
          </div>

          <div className="relative mx-auto animate-fade-up delay-200">
            <div className="relative w-80 h-80 rounded-full bg-gradient-to-br from-cyan-400/30 via-slate-900 to-slate-950 shadow-[0_20px_40px_rgba(0,0,0,0.5)] border border-cyan-400/30 flex items-center justify-center">
              <div className="absolute -top-4 right-0 bg-cyan-500 text-white rounded-full px-4 py-2 text-xs font-semibold shadow-lg">Talk to sales</div>
              <div className="w-56 h-52 bg-cyan-200/15 border border-cyan-300/25 rounded-3xl shadow-inner"></div>
            </div>
          </div>
        </section>

        <section id="trust" className="mt-16 animate-fade-up delay-300">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 sm:p-8">
            <h2 className="text-sm uppercase tracking-wider text-cyan-300">Trusted by</h2>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
              <div className="rounded-xl p-4 bg-slate-800/70 border border-slate-700">
                <p className="text-3xl font-bold text-white">600K+</p>
                <p className="text-slate-300">accounting professionals</p>
              </div>
              <div className="rounded-xl p-4 bg-slate-800/70 border border-slate-700">
                <p className="text-3xl font-bold text-white">30M+</p>
                <p className="text-slate-300">clients managed</p>
              </div>
              <div className="rounded-xl p-4 bg-slate-800/70 border border-slate-700">
                <p className="text-3xl font-bold text-white">25+</p>
                <p className="text-slate-300">years of industry experience</p>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="mt-16">
          <h2 className="text-3xl font-extrabold text-white animate-fade-up delay-400">Key features for accounting practices</h2>
          <p className="mt-2 text-slate-300 max-w-2xl animate-fade-up delay-450">Everything your firm needs to deliver fast, accurate, and high-value work for every client.</p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {[
              ['Client onboarding in minutes', 'Auto-import clients from file and bank connections with recommended settings.'],
              ['Automated tax workflows', 'Built-in checklists, return pre-fill, and e-file updates for every jurisdiction.'],
              ['Real-time firm dashboards', 'Single view of cash, WIP, margin, and KPIs across all clients.'],
              ['Secure collaboration', 'Role-based access controls with audit trails and encrypted documents.'],
              ['Proposals & billing', 'Create packages, proposals, and invoices in one workflow.'],
              ['AI-based insights', 'Client health alerts and tax savings recommendations each day.'],
            ].map(([title, description], idx) => (
              <article key={idx} className={`rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg animate-fade-up delay-${(idx + 1) * 50}`}>
                <h3 className="font-semibold text-white">{title}</h3>
                <p className="text-slate-300 mt-2">{description}</p>
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800 px-4 sm:px-6 py-10">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <h4 className="font-semibold text-white mb-3">Product</h4>
            <ul className="space-y-1 text-slate-400 text-sm"><li><a href="#">Overview</a></li><li><a href="#">Workflow</a></li><li><a href="#">Reporting</a></li></ul>
          </div>
          <div>
            <h4 className="font-semibold text-white mb-3">Company</h4>
            <ul className="space-y-1 text-slate-400 text-sm"><li><a href="#">About</a></li><li><a href="#">Careers</a></li><li><a href="#">Partners</a></li></ul>
          </div>
          <div>
            <h4 className="font-semibold text-white mb-3">Resources</h4>
            <ul className="space-y-1 text-slate-400 text-sm"><li><a href="#">Blog</a></li><li><a href="#">Help Center</a></li><li><a href="#">Community</a></li></ul>
          </div>
          <div>
            <h4 className="font-semibold text-white mb-3">Legal</h4>
            <ul className="space-y-1 text-slate-400 text-sm"><li><a href="#">Terms</a></li><li><a href="#">Privacy</a></li><li><a href="#">Security</a></li></ul>
          </div>
        </div>
        <p className="mt-8 text-slate-500 text-sm">© 2026 QuickBooks Accountants Clone</p>
      </footer>

      <style jsx global>{`
        .animate-fade-up { opacity: 0; transform: translateY(24px); animation: fadeUp 0.8s ease forwards; }
        .delay-200 { animation-delay: 0.2s; }
        .delay-300 { animation-delay: 0.3s; }
        .delay-400 { animation-delay: 0.4s; }
        .delay-450 { animation-delay: 0.45s; }
        .delay-500 { animation-delay: 0.5s; }

        @keyframes fadeUp {
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
