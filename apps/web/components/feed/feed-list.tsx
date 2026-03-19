import { FeedRow, type FeedRowModel } from "./feed-row";

export function FeedList({ posts }: { posts: FeedRowModel[] }) {
  return (
    <section>
      {posts.map((post, index) => (
        <FeedRow key={post.id} post={post} rank={index + 1} />
      ))}
    </section>
  );
}
