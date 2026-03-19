"use client";

import { useState } from "react";

type FormFieldProps = {
  label: string;
  type?: "text" | "email" | "password" | "datetime-local";
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  error?: string | null;
  hint?: string;
};

export function FormField({
  label,
  type = "text",
  value,
  onChange,
  placeholder,
  error,
  hint,
}: FormFieldProps) {
  const [focused, setFocused] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const isPassword = type === "password";

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-4">
        <label
          className={[
            "font-mono text-(length:--fs-label) uppercase tracking-[0.14em] transition-colors",
            focused ? "text-(--color-accent)" : "text-(--color-text-muted)",
          ].join(" ")}
        >
          {label}
        </label>
        {hint ? (
          <span className="font-mono text-(length:--fs-label) text-(--color-text-dim)">
            {hint}
          </span>
        ) : null}
      </div>

      <div className="relative">
        <input
          type={isPassword && revealed ? "text" : type}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className={[
            "w-full border bg-(--color-bg) px-4 py-4 font-mono text-(length:--fs-body-input) text-(--color-text) outline-none transition-colors",
            isPassword ? "pr-14" : "",
            error
              ? "border-(--color-error)"
              : focused
                ? "border-(--color-accent)"
                : "border-(--color-border)",
          ].join(" ")}
        />
        {isPassword ? (
          <button
            type="button"
            onClick={() => setRevealed((current) => !current)}
            className="absolute right-4 top-1/2 -translate-y-1/2 font-mono text-(length:--fs-meta) text-(--color-text-dim) transition-colors hover:text-(--color-accent)"
          >
            {revealed ? "hide" : "show"}
          </button>
        ) : null}
      </div>

      {error ? (
        <span className="font-mono text-(length:--fs-label) text-(--color-error)">
          ↳ {error}
        </span>
      ) : null}
    </div>
  );
}
