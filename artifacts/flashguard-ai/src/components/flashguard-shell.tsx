import { type ReactNode, useState } from 'react';
import {
  Activity,
  ArrowUpRight,
  BellRing,
  BookOpen,
  ChevronRight,
  CircleHelp,
  Compass,
  FileText,
  Layers3,
  Menu,
  Mountain,
  PanelLeftClose,
  ShieldCheck,
  X,
} from 'lucide-react';

type DestinationKey = 'foundation' | 'citizen' | 'officials' | 'pipeline' | 'protocols';

type FlashGuardShellProps = {
  children: ReactNode;
  activeDestination: DestinationKey;
  onNavigate: (destination: DestinationKey) => void;
};

const navItems: Array<{
  key: DestinationKey;
  label: string;
  note: string;
  icon: typeof Compass;
  state: 'active' | 'planned';
}> = [
  { key: 'foundation', label: 'Foundation', note: 'Phase 1 overview', icon: Compass, state: 'active' },
  { key: 'citizen', label: 'Citizen experience', note: 'Planned destination', icon: BellRing, state: 'planned' },
  { key: 'officials', label: 'Official console', note: 'Planned destination', icon: Activity, state: 'planned' },
];

function BrandMark() {
  return (
    <div className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-cyan-300/30 bg-cyan-300/10 text-cyan-200">
      <Mountain size={19} strokeWidth={1.8} />
      <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-amber-300 shadow-[0_0_0_3px_hsl(215_42%_6%)]" />
    </div>
  );
}

function SidebarContent({
  activeDestination,
  onNavigate,
  onClose,
}: {
  activeDestination: DestinationKey;
  onNavigate: (destination: DestinationKey) => void;
  onClose?: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-5 pb-8 pt-6">
        <button
          type="button"
          onClick={() => onNavigate('foundation')}
          className="flex items-center gap-3 text-left"
          data-testid="button-brand-home"
          aria-label="Go to FlashGuard foundation"
        >
          <BrandMark />
          <span>
            <span className="block text-[13px] font-extrabold tracking-[0.11em] text-slate-100">FLASHGUARD</span>
            <span className="mt-0.5 block font-mono text-[9px] tracking-[0.24em] text-cyan-300/70">AI / INDIA</span>
          </span>
        </button>
        {onClose ? (
          <button
            type="button"
            className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-white/[0.06] hover:text-slate-200 lg:hidden"
            onClick={onClose}
            data-testid="button-close-navigation"
            aria-label="Close navigation"
          >
            <X size={17} />
          </button>
        ) : null}
      </div>

      <div className="px-3">
        <div className="mb-3 flex items-center justify-between px-2">
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Workspace</span>
          <span className="rounded-full border border-amber-300/20 bg-amber-300/[0.07] px-2 py-1 font-mono text-[9px] uppercase tracking-[0.12em] text-amber-200/80">
            Phase 1
          </span>
        </div>
        <nav aria-label="Primary navigation" className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeDestination === item.key;
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => {
                  onNavigate(item.key);
                  onClose?.();
                }}
                className={`group flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left transition-all ${
                  isActive
                    ? 'border-cyan-200/20 bg-cyan-300/[0.1] text-cyan-100'
                    : 'border-transparent text-slate-400 hover:border-slate-700/70 hover:bg-white/[0.035] hover:text-slate-200'
                }`}
                data-testid={`nav-${item.key}`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon size={17} strokeWidth={isActive ? 2 : 1.7} className={isActive ? 'text-cyan-300' : 'text-slate-500'} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[12px] font-semibold">{item.label}</span>
                  <span className={`mt-0.5 block truncate font-mono text-[9px] ${isActive ? 'text-cyan-200/60' : 'text-slate-600'}`}>
                    {item.note}
                  </span>
                </span>
                {item.state === 'planned' ? (
                  <span className="font-mono text-[8px] uppercase tracking-[0.1em] text-slate-600">Soon</span>
                ) : (
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-300 shadow-[0_0_10px_rgba(103,232,249,0.8)]" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="mt-8 px-3">
        <div className="mb-3 px-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">System map</div>
        <div className="space-y-1">
          {[
            { key: 'pipeline' as DestinationKey, label: 'Signal pipeline', icon: Layers3 },
            { key: 'protocols' as DestinationKey, label: 'Safety protocols', icon: ShieldCheck },
          ].map((item) => {
            const Icon = item.icon;
            const isActive = activeDestination === item.key;
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => {
                  onNavigate(item.key);
                  onClose?.();
                }}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[12px] transition-colors ${
                  isActive ? 'bg-slate-800/80 text-slate-100' : 'text-slate-500 hover:bg-white/[0.035] hover:text-slate-300'
                }`}
                data-testid={`nav-${item.key}`}
              >
                <Icon size={16} className={isActive ? 'text-cyan-300' : 'text-slate-600'} />
                <span className="flex-1">{item.label}</span>
                <ChevronRight size={14} className="text-slate-700" />
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-auto px-4 pb-5">
        <div className="rounded-2xl border border-slate-800/90 bg-slate-900/70 p-3.5">
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-300/10 text-amber-200">
              <FileText size={14} />
            </div>
            <div>
              <div className="text-[11px] font-semibold text-slate-200">Prototype notes</div>
              <div className="font-mono text-[9px] text-slate-600">READ BEFORE EXTENDING</div>
            </div>
          </div>
          <p className="text-[11px] leading-relaxed text-slate-500">
            No live data, forecast, or alert delivery is connected in this phase.
          </p>
          <button
            type="button"
            onClick={() => onNavigate('foundation')}
            className="mt-3 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-cyan-300 transition-colors hover:text-cyan-100"
            data-testid="button-read-prototype-notes"
          >
            Review boundary <ArrowUpRight size={12} />
          </button>
        </div>
      </div>
    </div>
  );
}

export function FlashGuardShell({ children, activeDestination, onNavigate }: FlashGuardShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="fg-noise min-h-[100dvh] bg-background text-foreground">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[248px] border-r border-sidebar-border bg-sidebar lg:block">
        <SidebarContent activeDestination={activeDestination} onNavigate={onNavigate} />
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-slate-950/75 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
            data-testid="button-close-navigation-backdrop"
            aria-label="Close navigation backdrop"
          />
          <aside className="relative h-full w-[min(86vw,300px)] border-r border-sidebar-border bg-sidebar shadow-2xl">
            <SidebarContent activeDestination={activeDestination} onNavigate={onNavigate} onClose={() => setMobileOpen(false)} />
          </aside>
        </div>
      ) : null}

      <div className="lg:pl-[248px]">
        <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-[hsl(214_39%_7%/.82)] backdrop-blur-xl">
          <div className="flex h-[68px] items-center justify-between px-4 sm:px-7 lg:px-10">
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="rounded-lg border border-slate-700/80 p-2 text-slate-400 transition-colors hover:border-cyan-300/30 hover:text-cyan-200 lg:hidden"
                onClick={() => setMobileOpen(true)}
                data-testid="button-open-navigation"
                aria-label="Open navigation"
              >
                <Menu size={18} />
              </button>
              <div className="hidden items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500 sm:flex">
                <span className="text-cyan-300/70">FG / 01</span>
                <span className="text-slate-700">•</span>
                <span>Architecture workspace</span>
              </div>
              <div className="flex items-center gap-2 sm:hidden">
                <BrandMark />
                <span className="font-mono text-[10px] font-medium tracking-[0.12em] text-slate-300">FLASHGUARD / 01</span>
              </div>
            </div>
            <div className="flex items-center gap-2.5">
              <div className="hidden items-center gap-2 rounded-full border border-amber-300/15 bg-amber-300/[0.06] px-3 py-1.5 sm:flex" data-testid="status-prototype-phase">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-300" />
                <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-amber-100/75">Prototype boundary</span>
              </div>
              <button
                type="button"
                className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-white/[0.05] hover:text-slate-200"
                onClick={() => onNavigate('protocols')}
                data-testid="button-open-help"
                aria-label="Open safety protocols"
              >
                <CircleHelp size={17} />
              </button>
              <div className="hidden h-7 w-px bg-slate-800 sm:block" />
              <div className="flex items-center gap-2" data-testid="status-region-scope">
                <span className="hidden font-mono text-[9px] uppercase tracking-[0.14em] text-slate-600 sm:block">Initial scope</span>
                <span className="rounded-md border border-slate-700 bg-slate-900/80 px-2 py-1 font-mono text-[10px] text-slate-300">IN • 02</span>
              </div>
            </div>
          </div>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}