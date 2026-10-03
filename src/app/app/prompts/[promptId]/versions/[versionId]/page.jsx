"use client";

import { useEffect, use } from "react";
import { useRouter } from "next/navigation";

export default function PromptVersionRedirect({ params }) {
  const unwrappedParams = use(params);
  const router = useRouter();

  useEffect(() => {
    router.replace(`/app/prompts/${unwrappedParams.promptId}?tab=versions&versionId=${unwrappedParams.versionId}`);
  }, [router, unwrappedParams.promptId, unwrappedParams.versionId]);

  return (
    <div className="py-24 text-center text-slate-500 text-xs">
      Navigating to version {unwrappedParams.versionId}...
    </div>
  );
}
