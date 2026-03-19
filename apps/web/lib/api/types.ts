export type PageInfo = {
  next_cursor: string | null;
  has_next_page: boolean;
};

export type UserSummary = {
  id: string;
  username: string;
};

export type UserPayload = {
  id: string;
  username: string;
  bio: string | null;
  role: "user" | "moderator" | "admin";
  status: "pending" | "active" | "suspended" | "banned";
  karma: number;
  post_count: number;
  comment_count: number;
  avatar_url: string | null;
  created_at: string;
  last_active_at: string | null;
};

export type DomainSummary = {
  id: string;
  hostname: string;
  display_name: string | null;
};

export type PostPayload = {
  id: string;
  title: string;
  slug: string;
  post_type: "text" | "link" | "job";
  category: string;
  status: string;
  url: string | null;
  body_markdown: string | null;
  author: UserSummary;
  domain: DomainSummary | null;
  upvote_count: number;
  downvote_count: number;
  comment_count: number;
  score: number;
  rank_score: number;
  viewer_vote: number | null;
  viewer_can_edit: boolean;
  viewer_can_moderate: boolean;
  submitted_at: string;
  created_at: string;
  updated_at: string;
  last_commented_at: string | null;
  job_expires_at: string | null;
};

export type FeedResponse = {
  items: PostPayload[];
  page_info: PageInfo;
};

export type CommentPayload = {
  id: string;
  post_id: string;
  parent_comment_id: string | null;
  depth: number;
  body_markdown: string;
  status: string;
  author: UserSummary;
  upvote_count: number;
  downvote_count: number;
  score: number;
  rank_score: number;
  viewer_vote: 1 | -1 | null;
  viewer_can_edit: boolean;
  viewer_can_moderate: boolean;
  created_at: string;
  updated_at: string;
};

export type PostResponse = {
  post: PostPayload;
};

export type CommentResponse = {
  comment: CommentPayload;
};

export type CommentListResponse = {
  items: CommentPayload[];
  page_info: PageInfo;
};

export type PostVotePayload = {
  id: string;
  upvote_count: number;
  downvote_count: number;
  score: number;
  rank_score: number;
  viewer_vote: 1 | -1 | null;
};

export type CommentVotePayload = {
  id: string;
  upvote_count: number;
  downvote_count: number;
  score: number;
  rank_score: number;
  viewer_vote: 1 | -1 | null;
};

export type PostVoteResponse = {
  post: PostVotePayload;
};

export type CommentVoteResponse = {
  comment: CommentVotePayload;
};

export type PlatformSummary = {
  builders_this_month: number;
  builders_delta_pct: number | null;
  funding_stories_last_30d: number;
  funding_stories_delta_pct: number | null;
  posts_per_hour: number;
  posts_per_hour_delta_pct: number | null;
  comments_this_week: number;
  comments_delta_pct: number | null;
  jobs_live: number;
  jobs_live_delta_pct: number | null;
};

export type RegisterResponse = {
  verification_required: boolean;
  user: UserPayload;
};

export type AuthenticatedResponse = {
  user: UserPayload;
};
