interface OpsPlaceholderProps {
  code: string;
  title: string;
  description: string;
}

export default function OpsPlaceholder({
  code,
  title,
  description,
}: OpsPlaceholderProps) {
  return (
    <section className="max-w-6xl mx-auto">
      <div className="rounded-2xl border border-line bg-card p-8 shadow-sm">
        <div className="inline-flex items-center rounded-full bg-brand-light px-3 py-1 text-xs font-semibold text-ink">
          {code}
        </div>
        <h1 className="mt-4 text-2xl font-semibold text-ink">{title}</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-secondary">
          {description}
        </p>
        <div className="mt-8 rounded-xl border border-dashed border-line bg-surface px-6 py-12 text-center text-sm text-ink-muted">
          页面内容将在后续对应 Step 接入
        </div>
      </div>
    </section>
  );
}
