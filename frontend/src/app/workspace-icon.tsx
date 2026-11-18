export function WorkspaceIcon({
  name,
  className = "size-6",
}: {
  name: string;
  className?: string;
}) {
  return (
    <span
      aria-hidden="true"
      className={`relative inline-block shrink-0 overflow-hidden align-middle ${className}`}
    >
      <img
        alt=""
        src={`/icons/${name}.png`}
        className="absolute top-1/2 left-1/2 w-[148%] max-w-none -translate-1/2"
      />
    </span>
  );
}
