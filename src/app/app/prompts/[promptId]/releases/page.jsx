"use client";

import { useEffect, use } from "react";
import { useRouter } from "next/navigation";

export default function PromptReleasesRedirect({ params }) {
  const unwrappedParams = use(params);
  const router = useRouter();

  useEffect(() => {
    router.replace(`/app/prompts/${unwrappedParams.promptId}?tab=releases`);
  }, [router, unwrappedParams.promptId]);

  return (
    <div className="py-24 text-center text-slate-500 text-xs">
      Navigating to releases...
    </div>
  );
}
