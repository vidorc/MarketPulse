import clsx from "@/lib/clsx";
import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "ghost" | "subtle" | "danger";

const VARIANTS: Record<Variant, string> = {
  // Gold gradient with a soft glow — the single high-emphasis action.
  primary:
    "border-transparent bg-gradient-to-b from-gold-bright to-gold text-ground font-semibold shadow-glow hover:from-gold hover:to-gold hover:brightness-105",
  ghost:
    "border-line bg-transparent text-ink-soft hover:border-line-bright hover:bg-panel-2",
  subtle:
    "border-line/60 bg-panel-2 text-ink-soft hover:bg-elevated hover:border-line-bright",
  danger: "border-neg/40 bg-neg/10 text-neg hover:bg-neg/20",
};

export function Button({
  variant = "ghost",
  className,
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-1.5 rounded-md border px-3.5 py-1.5 text-[12px] font-medium tracking-wide transition-all duration-150 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-40",
        VARIANTS[variant],
        className
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
