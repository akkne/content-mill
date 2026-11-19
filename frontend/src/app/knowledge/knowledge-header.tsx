import { WorkspaceIcon } from "@/app/workspace-icon";

export function KnowledgeHeader({ project, description }: { project?: string; description: string }) {
  return (
    <header className="relative isolate mb-6 overflow-hidden rounded-[22px] border border-line bg-hero px-6 py-7 shadow-panel sm:px-8 sm:py-9 motion-safe:animate-[overview-appear_.24s_ease-out]">
      <div className="relative z-10 sm:pr-40">
        {project && <p className="mb-2 break-words text-xs font-bold text-accent">{project}</p>}
        <h1 className="text-3xl leading-tight font-bold tracking-tight sm:text-4xl">База знаний</h1>
        <p className="mt-3 max-w-lg text-sm leading-relaxed text-muted">{description}</p>
      </div>
      <div aria-hidden="true" className="absolute inset-y-0 right-10 hidden w-28 items-center justify-center sm:flex">
        <span className="absolute size-24 translate-x-4 -translate-y-2 rotate-12 rounded-3xl border border-accent/20 bg-tint" />
        <span className="relative grid size-24 -rotate-6 place-items-center rounded-3xl border border-line bg-tag shadow-panel">
          <WorkspaceIcon name="brand" className="size-20" />
        </span>
      </div>
    </header>
  );
}
