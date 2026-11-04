import { useState } from 'react';
import {
  ArrowDown,
  ArrowRight,
  BadgeInfo,
  BellRing,
  Check,
  ChevronDown,
  CloudRain,
  Code2,
  Database,
  FileCheck2,
  Gauge,
  Globe2,
  Landmark,
  LockKeyhole,
  Map,
  Radio,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  UsersRound,
  Workflow,
  X,
} from 'lucide-react';
import { FlashGuardShell } from '@/components/flashguard-shell';

type DestinationKey = 'foundation' | 'citizen' | 'officials' | 'pipeline' | 'protocols';

type Destination = {
  key: Exclude<DestinationKey, 'foundation'>;
  eyebrow: string;
  title: string;
  description: string;
  icon: typeof BellRing;
  detail: string;
  next: string;
  tone: 'cyan' | 'amber' | 'violet' | 'green';
};

const destinations: Destination[] = [
  {
    key: 'citizen',
    eyebrow: 'Future surface / 01',
    title: 'Citizen experience',
    description: 'A calm, accessible layer for people living and travelling in vulnerable terrain.',
    icon: UsersRound,
    detail: 'Will translate verified system outputs into understandable guidance without exposing unvalidated model signals.',
    next: 'Service design and language testing',
    tone: 'cyan',
  },
  {
    key: 'officials',
    eyebrow: 'Future surface / 02',
    title: 'Official console',
    description: 'A decision-support workspace for disaster-management teams and local authorities.',
    icon: Landmark,
    detail: 'Will keep source context, confidence, acknowledgement, and handoff visible to the people responsible for action.',
    next: 'Operational workflow mapping',
    tone: 'amber',
  },
  {
    key: 'pipeline',
    eyebrow: 'Future service / 03',
    title: 'Signal pipeline',
    description: 'The software boundary between environmental inputs, model services, and human review.',
    icon: Workflow,
    detail: 'Will make data provenance and model versioning inspectable before any signal can become an alert.',
    next: 'Input contracts and evaluation plan',
    tone: 'violet',
  },
  {
    key: 'protocols',
    eyebrow: 'Future guardrail / 04',
    title: 'Safety protocols',
    description: 'The non-negotiable checks around interpretation, escalation, and public communication.',
    icon: ShieldCheck,
    detail: 'Will define what the system can say, what it must withhold, and where human authority remains final.',
    next: 'Governance review',
    tone: 'green',
  },
];

const toneStyles = {
  cyan: {
    icon: 'border-cyan-300/20 bg-cyan-300/10 text-cyan-200',
    line: 'bg-cyan-300',
    chip: 'border-cyan-300/20 bg-cyan-300/[0.07] text-cyan-200/80',
  },
  amber: {
    icon: 'border-amber-300/20 bg-amber-300/10 text-amber-200',
    line: 'bg-amber-300',
    chip: 'border-amber-300/20 bg-amber-300/[0.07] text-amber-200/80',
  },
  violet: {
    icon: 'border-violet-300/20 bg-violet-300/10 text-violet-200',
    line: 'bg-violet-300',
    chip: 'border-violet-300/20 bg-violet-300/[0.07] text-violet-200/80',
  },
  green: {
    icon: 'border-emerald-300/20 bg-emerald-300/10 text-emerald-200',
    line: 'bg-emerald-300',
    chip: 'border-emerald-300/20 bg-emerald-300/[0.07] text-emerald-200/80',
  },
};

function SectionLabel({ children, index }: { children: string; index: string }) {
  return (
    <div className="mb-5 flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
      <span className="text-cyan-300/70">{index}</span>
      <span className="h-px w-7 bg-slate-700" />
      <span>{children}</span>
    </div>
  );
}

function FoundationPage() {
  const [activeDestination, setActiveDestination] = useState<DestinationKey>('foundation');
  const [scopeOpen, setScopeOpen] = useState(false);

  const handleNavigate = (destination: DestinationKey) => {
    setActiveDestination(destination);
    if (destination === 'foundation') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    window.requestAnimationFrame(() => {
      document.getElementById('architecture')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  };

  const selectedDestination = destinations.find((item) => item.key === activeDestination) ?? destinations[0];
  const SelectedIcon = selectedDestination.icon;
  const selectedTone = toneStyles[selectedDestination.tone];

  return (
    <FlashGuardShell activeDestination={activeDestination} onNavigate={handleNavigate}>
      <div className="mx-auto max-w-[1480px] px-4 pb-16 sm:px-7 lg:px-10">
        <div className="flex items-center justify-between border-b border-slate-800/70 py-4">
          <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.16em] text-slate-600">
            <span>Foundation</span>
            <ArrowRight size={12} className="text-slate-700" />
            <span className="text-slate-400">Architecture</span>
          </div>
          <span className="font-mono text-[10px] text-slate-600" data-testid="text-foundation-version">
            BUILD 0.1 / STATIC SHELL
          </span>
        </div>

        <section className="relative grid gap-10 pb-16 pt-12 lg:grid-cols-[minmax(0,1fr)_minmax(330px,0.72fr)] lg:items-center lg:gap-16 lg:pb-24 lg:pt-20">
          <div className="pointer-events-none absolute -left-10 top-10 h-56 w-56 rounded-full bg-cyan-300/[0.035] blur-3xl" />
          <div className="relative animate-rise">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/[0.06] px-3 py-1.5" data-testid="status-foundation-ready">
              <Sparkles size={13} className="text-cyan-300" />
              <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-cyan-100/80">Foundation online / no live feeds</span>
            </div>
            <h1 className="max-w-[740px] text-balance text-[clamp(2.75rem,6vw,5.8rem)] font-extrabold leading-[0.98] tracking-[-0.065em] text-slate-100">
              Read the terrain
              <span className="block text-cyan-300">before it moves.</span>
            </h1>
            <p className="mt-7 max-w-[650px] text-[15px] leading-7 text-slate-400 sm:text-[17px] sm:leading-8">
              FlashGuard AI is a software-only early-warning concept for flash-flood risk in India&apos;s hilly regions. This Phase 1 shell establishes the surfaces, boundaries, and safety thinking that future experiences will build on.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => handleNavigate('citizen')}
                className="group inline-flex items-center gap-2 rounded-lg bg-cyan-300 px-4 py-3 text-[12px] font-bold text-slate-950 transition-transform hover:-translate-y-0.5"
                data-testid="button-explore-architecture"
              >
                Explore architecture
                <ArrowDown size={15} className="transition-transform group-hover:translate-y-0.5" />
              </button>
              <button
                type="button"
                onClick={() => setScopeOpen((open) => !open)}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-3 text-[12px] font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-slate-100"
                data-testid="button-toggle-scope-notes"
                aria-expanded={scopeOpen}
              >
                What exists in Phase 1
                <ChevronDown size={15} className={`transition-transform ${scopeOpen ? 'rotate-180' : ''}`} />
              </button>
            </div>
            {scopeOpen ? (
              <div className="mt-5 max-w-[650px] rounded-xl border border-amber-300/20 bg-amber-300/[0.055] p-4 animate-rise" data-testid="panel-phase-one-scope">
                <div className="flex gap-3">
                  <BadgeInfo size={17} className="mt-0.5 shrink-0 text-amber-200" />
                  <p className="text-[12px] leading-6 text-amber-100/75">
                    This release is a navigable frontend foundation only. It contains no prediction dashboard, live map, machine-learning result, alert, authentication, or real-time API.
                  </p>
                  <button
                    type="button"
                    onClick={() => setScopeOpen(false)}
                    className="ml-auto self-start rounded-md p-1 text-amber-100/50 hover:bg-amber-100/10 hover:text-amber-100"
                    data-testid="button-close-scope-notes"
                    aria-label="Close Phase 1 scope notes"
                  >
                    <X size={14} />
                  </button>
                </div>
              </div>
            ) : null}
            <div className="mt-9 flex flex-wrap items-center gap-2.5" data-testid="list-initial-regions">
              <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-slate-600">Initial regional focus</span>
              <span className="rounded-md border border-slate-700/80 bg-slate-900/70 px-2.5 py-1.5 text-[11px] font-semibold text-slate-300">Uttarakhand</span>
              <span className="rounded-md border border-slate-700/80 bg-slate-900/70 px-2.5 py-1.5 text-[11px] font-semibold text-slate-300">Sikkim</span>
            </div>
          </div>

          <div className="relative animate-rise animate-rise-delay-1">
            <div className="overflow-hidden rounded-[22px] border border-slate-700/80 bg-slate-900/80 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3.5">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-amber-300" />
                  <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-slate-400">System pulse</span>
                </div>
                <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-slate-600">Awaiting integration</span>
              </div>
              <div className="relative flex min-h-[315px] flex-col justify-between overflow-hidden p-5 sm:p-7">
                <div className="pointer-events-none absolute inset-0 opacity-50" style={{ backgroundImage: 'linear-gradient(rgba(106, 174, 194, .06) 1px, transparent 1px), linear-gradient(90deg, rgba(106, 174, 194, .06) 1px, transparent 1px)', backgroundSize: '28px 28px' }} />
                <div className="relative flex items-start justify-between">
                  <div>
                    <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-600">Readiness state</div>
                    <div className="mt-2 text-2xl font-bold tracking-[-0.04em] text-slate-200" data-testid="status-no-live-signal">No live signal</div>
                  </div>
                  <Radio size={20} className="text-slate-600" />
                </div>
                <div className="relative mx-auto my-7 flex h-36 w-36 items-center justify-center">
                  <div className="absolute inset-0 rounded-full border border-cyan-300/10" />
                  <div className="absolute inset-5 rounded-full border border-cyan-300/15" />
                  <div className="absolute inset-10 rounded-full border border-cyan-300/20" />
                  <div className="absolute h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_20px_rgba(103,232,249,.9)]" />
                  <div className="absolute h-px w-full rotate-[22deg] bg-gradient-to-r from-transparent via-cyan-300/50 to-transparent" />
                  <div className="absolute h-full w-px rotate-[22deg] bg-gradient-to-b from-transparent via-cyan-300/40 to-transparent" />
                </div>
                <div className="relative grid grid-cols-3 gap-2 border-t border-slate-800 pt-4">
                  {['Inputs', 'Models', 'Outreach'].map((label, index) => (
                    <div key={label} data-testid={`status-pulse-${label.toLowerCase()}`}>
                      <div className="mb-1.5 flex items-center gap-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-slate-600" />
                        <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-slate-600">{label}</span>
                      </div>
                      <div className="font-mono text-[10px] text-slate-500">{index === 0 ? 'UNWIRED' : 'PLANNED'}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="mt-3 flex items-center justify-between px-1 font-mono text-[9px] uppercase tracking-[0.14em] text-slate-600">
              <span>Architecture preview</span>
              <span>Not a forecast</span>
            </div>
          </div>
        </section>

        <section className="border-t border-slate-800/80 py-16 lg:py-20" id="architecture">
          <SectionLabel index="01" children="A system with clear handoffs" />
          <div className="grid gap-8 lg:grid-cols-[0.75fr_1.25fr] lg:gap-16">
            <div>
              <h2 className="max-w-[420px] text-3xl font-bold tracking-[-0.045em] text-slate-100 sm:text-4xl" data-testid="heading-architecture">
                Four destinations.
                <span className="block text-slate-500">One accountable thread.</span>
              </h2>
              <p className="mt-5 max-w-[390px] text-[13px] leading-6 text-slate-500">
                The product will separate public guidance from operational decision support, while keeping the path from signal to action inspectable.
              </p>
              <div className="mt-8 flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-3.5" data-testid="status-architecture-selection">
                <div className={`flex h-9 w-9 items-center justify-center rounded-lg border ${selectedTone.icon}`}>
                  <SelectedIcon size={17} />
                </div>
                <div className="min-w-0">
                  <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-slate-600">Selected surface</div>
                  <div className="truncate text-[12px] font-semibold text-slate-200">{selectedDestination.title}</div>
                </div>
                <span className={`ml-auto rounded-full border px-2 py-1 font-mono text-[8px] uppercase tracking-[0.1em] ${selectedTone.chip}`}>Planned</span>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {destinations.map((destination, index) => {
                const Icon = destination.icon;
                const tone = toneStyles[destination.tone];
                const isSelected = activeDestination === destination.key;
                return (
                  <button
                    key={destination.key}
                    type="button"
                    onClick={() => setActiveDestination(destination.key)}
                    className={`group relative overflow-hidden rounded-2xl border p-5 text-left transition-all duration-300 ${
                      isSelected
                        ? 'border-cyan-300/30 bg-slate-800/90 shadow-lg'
                        : 'border-slate-800 bg-slate-900/55 hover:-translate-y-0.5 hover:border-slate-600 hover:bg-slate-800/65'
                    }`}
                    data-testid={`card-destination-${destination.key}`}
                    aria-pressed={isSelected}
                  >
                    <div className={`absolute left-0 top-0 h-0.5 w-14 ${tone.line} ${isSelected ? 'opacity-100' : 'opacity-50'}`} />
                    <div className="flex items-start justify-between gap-4">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${tone.icon}`}>
                        <Icon size={18} strokeWidth={1.8} />
                      </div>
                      <span className="font-mono text-[10px] text-slate-700">0{index + 1}</span>
                    </div>
                    <div className="mt-7 font-mono text-[9px] uppercase tracking-[0.13em] text-slate-600">{destination.eyebrow}</div>
                    <h3 className="mt-2 text-[16px] font-bold tracking-[-0.025em] text-slate-100">{destination.title}</h3>
                    <p className="mt-2 text-[12px] leading-5 text-slate-500">{destination.description}</p>
                    <div className={`mt-5 flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-[0.12em] transition-colors ${isSelected ? 'text-cyan-300' : 'text-slate-600 group-hover:text-slate-400'}`}>
                      Inspect boundary <ArrowRight size={12} />
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
          <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6" data-testid="panel-selected-destination">
            <div className="grid gap-5 sm:grid-cols-[1fr_auto] sm:items-center">
              <div>
                <div className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-300" />
                  <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-cyan-200/70">Architecture note</span>
                </div>
                <p className="mt-3 max-w-3xl text-[13px] leading-6 text-slate-400">{selectedDestination.detail}</p>
              </div>
              <div className="border-l border-slate-800 pl-0 sm:min-w-[210px] sm:pl-6">
                <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-slate-600">Next design input</div>
                <div className="mt-2 text-[12px] font-semibold text-slate-300">{selectedDestination.next}</div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-8 border-t border-slate-800/80 py-16 lg:grid-cols-[0.7fr_1.3fr] lg:gap-16 lg:py-20" id="phase-notes">
          <div>
            <SectionLabel index="02" children="Design constraints" />
            <h2 className="max-w-[390px] text-3xl font-bold tracking-[-0.045em] text-slate-100 sm:text-4xl">
              Calm is a
              <span className="block text-cyan-300">safety feature.</span>
            </h2>
            <p className="mt-5 max-w-[380px] text-[13px] leading-6 text-slate-500">
              In a high-stakes interface, clarity is not decoration. Each future surface must make uncertainty legible and the next responsible action easy to find.
            </p>
          </div>
          <div className="divide-y divide-slate-800 rounded-2xl border border-slate-800 bg-slate-900/50">
            {[
              { icon: ShieldAlert, title: 'Never overstate confidence', text: 'Model output will be framed as decision support, with provenance and uncertainty visible by design.' },
              { icon: Map, title: 'Keep place at the center', text: 'Uttarakhand and Sikkim are the initial focus; later regional expansion should be an explicit decision.' },
              { icon: LockKeyhole, title: 'Human authority remains final', text: 'The system can inform a response, but it cannot replace local judgement, protocols, or accountable officials.' },
              { icon: FileCheck2, title: 'Ship the boundary before the signal', text: 'Phase 1 is deliberately limited to a dependable frontend architecture with no invented operational data.' },
            ].map((principle, index) => {
              const Icon = principle.icon;
              return (
                <div key={principle.title} className="flex gap-4 p-5 sm:gap-5 sm:p-6" data-testid={`row-principle-${index + 1}`}>
                  <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-slate-700 bg-slate-800/70 text-cyan-300">
                    <Icon size={16} strokeWidth={1.8} />
                  </div>
                  <div>
                    <h3 className="text-[13px] font-bold text-slate-200">{principle.title}</h3>
                    <p className="mt-1.5 max-w-xl text-[12px] leading-5 text-slate-500">{principle.text}</p>
                  </div>
                  <Check size={15} className="ml-auto mt-1 hidden shrink-0 text-slate-700 sm:block" />
                </div>
              );
            })}
          </div>
        </section>

        <section className="border-t border-slate-800/80 py-16 lg:py-20">
          <SectionLabel index="03" children="Ready for extension" />
          <div className="relative overflow-hidden rounded-[22px] border border-cyan-300/20 bg-[linear-gradient(120deg,rgba(32,108,124,.18),rgba(14,26,38,.82)_58%)] p-6 sm:p-9 lg:p-12">
            <div className="pointer-events-none absolute -right-24 -top-32 h-80 w-80 rounded-full border border-cyan-300/10" />
            <div className="pointer-events-none absolute -right-12 -top-20 h-56 w-56 rounded-full border border-cyan-300/10" />
            <div className="relative grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
              <div>
                <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.17em] text-cyan-200/75">
                  <Code2 size={14} />
                  <span>Frontend foundation / complete</span>
                </div>
                <h2 className="mt-5 max-w-2xl text-3xl font-bold tracking-[-0.045em] text-slate-100 sm:text-4xl">
                  The next signal should arrive to a system that knows its limits.
                </h2>
                <p className="mt-4 max-w-xl text-[13px] leading-6 text-slate-400">
                  The shell is ready to receive real, reviewed services in a later phase. Until then, every empty state is intentional.
                </p>
              </div>
              <button
                type="button"
                onClick={() => handleNavigate('protocols')}
                className="inline-flex w-fit items-center gap-2 rounded-lg border border-cyan-200/25 bg-cyan-200/[0.08] px-4 py-3 text-[12px] font-semibold text-cyan-100 transition-colors hover:bg-cyan-200/[0.14]"
                data-testid="button-review-safety-protocols"
              >
                Review safety layer <ArrowRight size={15} />
              </button>
            </div>
          </div>
        </section>

        <footer className="flex flex-col gap-3 border-t border-slate-800/80 pt-6 text-[10px] text-slate-600 sm:flex-row sm:items-center sm:justify-between" data-testid="footer-phase-metadata">
          <div className="flex items-center gap-2 font-mono uppercase tracking-[0.15em]">
            <Globe2 size={13} />
            <span>India / Hilly region focus</span>
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 font-mono uppercase tracking-[0.13em]">
            <span>Uttarakhand</span>
            <span className="text-slate-800">•</span>
            <span>Sikkim</span>
            <span className="text-slate-800">•</span>
            <span>Phase 1 / 2025</span>
          </div>
        </footer>
      </div>
    </FlashGuardShell>
  );
}

export default FoundationPage;