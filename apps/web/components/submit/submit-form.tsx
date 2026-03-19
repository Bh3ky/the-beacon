"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { BrowserApiError, fetchCurrentUser, submitPost } from "@/lib/browser-api";

import { FormField } from "../auth/form-field";

const CATEGORY_OPTIONS = [
  { value: "funding", label: "Funding" },
  { value: "launch", label: "Launch" },
  { value: "policy", label: "Policy" },
  { value: "opinion", label: "Opinion" },
  { value: "ask", label: "Ask" },
  { value: "show", label: "Show" },
  { value: "jobs", label: "Jobs" },
  { value: "engineering", label: "Engineering" },
  { value: "ecosystem", label: "Ecosystem" },
] as const;

type PostType = "link" | "text" | "job";

export function SubmitForm() {
  const router = useRouter();
  const [authLoading, setAuthLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [title, setTitle] = useState("");
  const [postType, setPostType] = useState<PostType>("link");
  const [category, setCategory] = useState("show");
  const [url, setUrl] = useState("");
  const [bodyMarkdown, setBodyMarkdown] = useState("");
  const [jobExpiresAt, setJobExpiresAt] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    void fetchCurrentUser()
      .then((user) => {
        if (!active) {
          return;
        }
        setIsAuthenticated(Boolean(user));
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setIsAuthenticated(false);
      })
      .finally(() => {
        if (active) {
          setAuthLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSubmitting(true);

    try {
      const response = await submitPost({
        post_type: postType,
        category,
        title,
        url: url || null,
        body_markdown: bodyMarkdown || null,
        job_expires_at: jobExpiresAt ? new Date(jobExpiresAt).toISOString() : null,
      });
      router.push(`/post/${response.post.id}/${response.post.slug}`);
      router.refresh();
    } catch (error) {
      if (error instanceof BrowserApiError) {
        setFormError(error.message);
      } else {
        setFormError("Submission failed. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (authLoading) {
    return (
      <div className="border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-8 font-mono text-[length:var(--fs-body-base)] text-[var(--color-text-dim)]">
        Checking session…
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-8">
        <h2 className="font-display text-[length:var(--fs-heading-form)] tracking-[-0.04em] text-[var(--color-text)]">
          Sign in to submit
        </h2>
        <p className="mt-4 max-w-2xl font-mono text-[length:var(--fs-body-base)] leading-7 text-[var(--color-text-dim)]">
          The submission surface is live, but posting still requires an authenticated
          session and CSRF token from the browser flow.
        </p>
        <div className="mt-8 flex gap-4">
          <Link
            href="/login"
            className="bg-[var(--color-accent)] px-6 py-4 font-mono text-[length:var(--fs-body-base)] font-bold uppercase tracking-[0.1em] text-[var(--color-nav-text-on-accent)]"
          >
            sign in
          </Link>
          <Link
            href="/register"
            className="border border-[var(--color-border-strong)] px-6 py-4 font-mono text-[length:var(--fs-body-base)] uppercase tracking-[0.1em] text-[var(--color-text-muted)]"
          >
            create account
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <div className="grid gap-8 lg:grid-cols-[1fr_14rem]">
        <div className="space-y-8">
          <FormField
            label="Title"
            value={title}
            onChange={setTitle}
            placeholder="What are you submitting?"
          />
          {(postType === "link" || postType === "job") && (
            <FormField
              label="URL"
              type="text"
              value={url}
              onChange={setUrl}
              placeholder="https://example.com/story"
            />
          )}
          {(postType === "text" || postType === "job") && (
            <div className="flex flex-col gap-2">
              <label className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.14em] text-[var(--color-text-muted)]">
                Body
              </label>
              <textarea
                value={bodyMarkdown}
                onChange={(event) => setBodyMarkdown(event.target.value)}
                placeholder="Add the context, thesis, or job details."
                className="min-h-[16rem] w-full border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-4 font-mono text-[length:var(--fs-body-input)] text-[var(--color-text)] outline-none transition-colors focus:border-[var(--color-accent)]"
              />
            </div>
          )}
        </div>

        <div className="space-y-8">
          <div className="flex flex-col gap-2">
            <label className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.14em] text-[var(--color-text-muted)]">
              Post type
            </label>
            <select
              value={postType}
              onChange={(event) => setPostType(event.target.value as PostType)}
              className="border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-4 font-mono text-[length:var(--fs-body-input)] text-[var(--color-text)] outline-none focus:border-[var(--color-accent)]"
            >
              <option value="link">link</option>
              <option value="text">text</option>
              <option value="job">job</option>
            </select>
          </div>

          <div className="flex flex-col gap-2">
            <label className="font-mono text-[length:var(--fs-label)] uppercase tracking-[0.14em] text-[var(--color-text-muted)]">
              Category
            </label>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-4 font-mono text-[length:var(--fs-body-input)] text-[var(--color-text)] outline-none focus:border-[var(--color-accent)]"
            >
              {CATEGORY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {postType === "job" ? (
            <FormField
              label="Job expires at"
              type="datetime-local"
              value={jobExpiresAt}
              onChange={setJobExpiresAt}
            />
          ) : null}
        </div>
      </div>

      {formError ? (
        <p className="font-mono text-[length:var(--fs-body-base)] text-[var(--color-error)]">
          {formError}
        </p>
      ) : null}

      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={submitting}
          className="bg-[var(--color-accent)] px-8 py-4 font-mono text-[length:var(--fs-body-base)] font-bold uppercase tracking-[0.1em] text-[var(--color-nav-text-on-accent)] transition-colors hover:bg-[var(--color-accent-hover)] disabled:cursor-wait disabled:bg-[var(--color-accent-dim)]"
        >
          {submitting ? "submitting…" : "submit post"}
        </button>
        <p className="font-mono text-[length:var(--fs-meta)] text-[var(--color-text-dim)]">
          Browser requests go through the same-origin proxy so cookies and CSRF stay intact.
        </p>
      </div>
    </form>
  );
}
