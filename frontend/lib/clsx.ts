/** Tiny classnames joiner — avoids a dependency for the one thing we need it for. */
export default function clsx(
  ...parts: Array<string | false | null | undefined>
): string {
  return parts.filter(Boolean).join(" ");
}
