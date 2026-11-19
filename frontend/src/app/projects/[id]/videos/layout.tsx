import { VideoShell } from "@/app/videos/video-shell";

export default function Layout({ children }: { children: React.ReactNode }) {
  return <VideoShell>{children}</VideoShell>;
}
