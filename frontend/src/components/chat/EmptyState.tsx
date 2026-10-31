export function EmptyState() {
  return (
    <div className="w-full max-w-2xl mx-auto text-center px-4 mb-8 select-none">
      {/* Main Headline */}
      <h1 className="font-serif text-3xl sm:text-4xl font-normal text-parchment-primary dark:text-darkpaper-primary tracking-tight mb-2.5">
        What would you like to research today?
      </h1>
      <p className="font-serif text-sm text-parchment-on-surface-variant dark:text-darkpaper-on-surface-variant max-w-md mx-auto leading-relaxed">
        Grounded academic inquiry across indexed PDFs using dense semantic search, Neo4j multi-hop graph reasoning, and verified citations.
      </p>
    </div>
  );
}
