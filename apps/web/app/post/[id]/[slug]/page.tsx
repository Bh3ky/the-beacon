import { notFound } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { SiteFooter } from "@/components/layout/site-footer";
import { CommentComposer } from "@/components/post/comment-composer-shell";
import { CommentThread } from "@/components/post/comment-thread";
import { PostHeader, PostHero } from "@/components/post/post-header";
import { ApiFetchError } from "@/lib/api/client";
import { getPostComments, getPostDetail } from "@/lib/api/posts";
import { buildCommentTree } from "@/lib/comments";

export default async function PostPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string; slug: string }>;
  searchParams?: Promise<{ sort?: "top" | "new" | "old" }>;
}) {
  const { id } = await params;
  const resolvedSearchParams = await searchParams;
  const sort = resolvedSearchParams?.sort ?? "top";

  try {
    const [postResponse, commentsResponse] = await Promise.all([
      getPostDetail(id),
      getPostComments(id, sort),
    ]);
    const post = postResponse.post;
    const comments = buildCommentTree(commentsResponse.items, {
      postAuthorUsername: post.author.username,
      sort,
    });

    return (
      <AppShell>
        <PostHeader post={post} />

        <main className="flex-1 px-6 pb-20 pt-10 sm:px-10">
          <div className="mx-auto max-w-344">
            <PostHero post={post} />
            <section className="border-b border-(--color-border) py-10">
              <div className="mt-6">
                <CommentComposer postId={post.id} buttonLabel="add comment" />
              </div>
            </section>

            <section className="pt-10">
              <div className="mb-8 flex flex-wrap items-center gap-6">
                <h2 className="font-mono text-(length:--fs-label) uppercase tracking-[0.32em] text-(--color-text-dim)">
                  {post.comment_count} comments
                </h2>
                <div className="flex items-center gap-5 font-mono text-(length:--fs-meta) text-(--color-text-dim)">
                  {(["top", "new", "old"] as const).map((option) => (
                    <a
                      key={option}
                      href={`?sort=${option}`}
                      className={
                        option === sort
                          ? "text-(--color-accent)"
                          : "transition-colors hover:text-(--color-accent)"
                      }
                    >
                      {option}
                    </a>
                  ))}
                </div>
              </div>

              <CommentThread comments={comments} />
            </section>
          </div>
        </main>

        <SiteFooter />
      </AppShell>
    );
  } catch (error) {
    if (error instanceof ApiFetchError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
